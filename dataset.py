"""Monta o dataset unificado de faturamento mensal por segmento e UF, em reais.

O IBGE nao publica faturamento mensal em R$. Ele publica:
- mensal: indice de receita nominal (PMC, PMS) ou de producao fisica (PIM-PF);
- anual: receita em mil reais por UF (PAC, PAS, PIA).

A estimativa junta os dois. Para cada segmento e UF:

    faturamento_mes = receita_anual[ANO_BASE] * indice_mes / soma(indices dos 12 meses de ANO_BASE)

Os 12 meses de ANO_BASE somam exatamente a receita anual oficial; os demais
meses seguem a variacao do indice mensal (inclusive a sazonalidade).

Na industria nao existe indice de receita: usa-se producao fisica (PIM-PF, por
UF) x indice de precos ao produtor (IPP, Brasil) como indice de receita nominal.

No agro nenhuma fonte oficial publica receita mensal por UF. O segmento
AGRO_EXPORTACAO usa a exportacao mensal de produtos agropecuarios (ISIC secao A)
por UF do Comex Stat (MDIC), em US$ FOB, convertida para R$ pelo cambio medio do
mes (BCB/SGS 3698). E receita de exportacao, nao o faturamento total do agro.

Fontes detalhadas em fontes.md.

Uso:
    python dataset.py
    python dataset.py --periodos 201501-202612
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

import sidra

PASTA_DADOS = Path(__file__).parent / "dados"

# Ultimo ano com PAC, PAS e PIA publicadas por UF (series novas).
ANO_BASE = 2024

# Numero-indice SEM ajuste sazonal: e o que carrega o nivel e a sazonalidade.
PMC_INDICE = 7169
PMS_INDICE = 7167
PIM_INDICE = 12606
IPP_INDICE = 10008

# Receita anual por UF, em mil reais.
PAC_RECEITA = 866  # receita bruta de revenda de mercadorias (tabela 10653)
PAS_RECEITA = 672  # receita bruta de servicos (tabela 10762)
PIA_RECEITA = 835  # total de receitas liquidas de vendas (tabela 10457)

# Agro: exportacao por UF de origem do produto (Comex Stat) e cambio (BCB).
COMEX_URL = "https://api-comexstat.mdic.gov.br/general"
BCB_DOLAR_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.3698/dados"  # media mensal, venda

# Cada segmento: (tabela, variavel, filtro de classificacao).
# nivel "setor": segmentos que nao se sobrepoem entre si.
# nivel "subsetor": abertura de SERVICOS e INDUSTRIA (nao somar com o setor).
SEGMENTOS = [
    {
        "nivel": "setor",
        "segmento": "COMERCIO_VAREJISTA",
        "indice": (8880, PMC_INDICE, "11046[56733]"),
        "receita": (10653, PAC_RECEITA, "11066[90084]"),
    },
    {
        "nivel": "setor",
        "segmento": "COMERCIO_VEICULOS",
        "indice": (8884, PMC_INDICE, "11046[56737]"),
        "receita": (10653, PAC_RECEITA, "11066[83357]"),
    },
    {
        "nivel": "setor",
        "segmento": "SERVICOS",
        "indice": (5906, PMS_INDICE, "11046[56725]"),
        "receita": (10762, PAS_RECEITA, "12355[107071]"),
    },
    {
        "nivel": "setor",
        "segmento": "INDUSTRIA",
        "indice": (8888, PIM_INDICE, "544[129314]"),
        "preco": (6903, IPP_INDICE, "842[46608]"),
        "receita": (10457, PIA_RECEITA, "12762[117897]"),
    },
    {
        "nivel": "subsetor",
        "segmento": "SERVICOS_FAMILIAS",
        "indice": (8693, PMS_INDICE, "11046[56725]|12355[106869]"),
        "receita": (10762, PAS_RECEITA, "12355[58296]"),
    },
    {
        "nivel": "subsetor",
        "segmento": "SERVICOS_INFORMACAO_COMUNICACAO",
        "indice": (8693, PMS_INDICE, "11046[56725]|12355[106874]"),
        "receita": (10762, PAS_RECEITA, "12355[106874]"),
    },
    {
        "nivel": "subsetor",
        "segmento": "SERVICOS_PROFISSIONAIS_ADMINISTRATIVOS",
        "indice": (8693, PMS_INDICE, "11046[56725]|12355[31399]"),
        "receita": (10762, PAS_RECEITA, "12355[31399]"),
    },
    {
        "nivel": "subsetor",
        "segmento": "SERVICOS_TRANSPORTES",
        "indice": (8693, PMS_INDICE, "11046[56725]|12355[106876]"),
        "receita": (10762, PAS_RECEITA, "12355[106876]"),
    },
    {
        # PMS "5. Outros servicos" ~ PAS imobiliarias + manutencao + outras.
        "nivel": "subsetor",
        "segmento": "SERVICOS_OUTROS",
        "indice": (8693, PMS_INDICE, "11046[56725]|12355[31426]"),
        "receita": (10762, PAS_RECEITA, "12355[9309,106882,106883]"),
    },
    {
        "nivel": "subsetor",
        "segmento": "INDUSTRIA_EXTRATIVA",
        "indice": (8888, PIM_INDICE, "544[129315]"),
        "preco": (6903, IPP_INDICE, "842[46609]"),
        "receita": (10457, PIA_RECEITA, "12762[116880]"),
    },
    {
        "nivel": "subsetor",
        "segmento": "INDUSTRIA_TRANSFORMACAO",
        "indice": (8888, PIM_INDICE, "544[129316]"),
        "preco": (6903, IPP_INDICE, "842[46610]"),
        "receita": (10457, PIA_RECEITA, "12762[116910]"),
    },
]

UF_SIGLA = {
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR",
    "Pará": "PA", "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA",
    "Piauí": "PI", "Ceará": "CE", "Rio Grande do Norte": "RN", "Paraíba": "PB",
    "Pernambuco": "PE", "Alagoas": "AL", "Sergipe": "SE", "Bahia": "BA",
    "Minas Gerais": "MG", "Espírito Santo": "ES", "Rio de Janeiro": "RJ",
    "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
}


def serie(fonte, periodos, localidades="N3[all]"):
    """Baixa uma variavel e soma as categorias do filtro. Colunas: localidade, periodo, valor."""
    tabela, variavel, classificacao = fonte
    payload = sidra.buscar(
        tabela,
        periodos=periodos,
        localidades=localidades,
        classificacoes=classificacao.split("|"),
        variaveis=variavel,
    )
    linhas = sidra.achatar(payload, tabela, "")
    if not linhas:
        return pd.DataFrame(columns=["localidade", "periodo", "valor"])

    df = pd.DataFrame(linhas)
    # min_count=1: sem nenhum valor numerico fica NaN, nao 0
    return df.groupby(["localidade", "periodo"])["valor"].sum(min_count=1).reset_index()


def estimar(config, periodos):
    indice = serie(config["indice"], periodos)

    if "preco" in config:
        preco = serie(config["preco"], periodos, localidades="N1[all]")
        indice = indice.merge(preco[["periodo", "valor"]], on="periodo", suffixes=("", "_preco"))
        indice["valor"] = indice["valor"] * indice["valor_preco"]

    indice = indice.dropna(subset=["valor"])

    receita = serie(config["receita"], str(ANO_BASE)).set_index("localidade")["valor"] * 1000

    base = indice[indice["periodo"].str.startswith(str(ANO_BASE))].groupby("localidade")["valor"]
    soma_base = base.sum()[base.count() == 12]  # so UFs com o ano base completo

    fator = receita / soma_base
    indice["valor"] = indice["valor"] * indice["localidade"].map(fator)

    return formatar(config["nivel"], config["segmento"], indice)


def agro_exportacao(periodos):
    """Exportacao mensal de produtos agropecuarios (ISIC A) por UF, em R$."""
    inicio, fim = periodos.split("-")
    corpo = {
        "flow": "export",
        "monthDetail": True,
        "period": {"from": f"{inicio[:4]}-{inicio[4:]}", "to": f"{fim[:4]}-{fim[4:]}"},
        "filters": [{"filter": "ISICSection", "values": ["A"]}],
        "details": ["state"],
        "metrics": ["metricFOB"],
    }
    resposta = requests.post(COMEX_URL, json=corpo, timeout=300)
    resposta.raise_for_status()
    df = pd.DataFrame(resposta.json()["data"]["list"])
    # descarta "Nao Declarada", "Reexportacao", "Consumo de Bordo" etc.
    df = df[df["state"].isin(UF_SIGLA)].rename(columns={"state": "localidade"})
    df["periodo"] = df["year"] + df["monthNumber"]

    params = {
        "formato": "json",
        "dataInicial": f"01/{inicio[4:]}/{inicio[:4]}",
        "dataFinal": f"01/{fim[4:]}/{fim[:4]}",  # serie mensal datada no dia 1
    }
    resposta = requests.get(BCB_DOLAR_URL, params=params, timeout=60)
    resposta.raise_for_status()
    # data vem como DD/MM/AAAA
    dolar = {c["data"][6:] + c["data"][3:5]: float(c["valor"]) for c in resposta.json()}

    df["valor"] = df["metricFOB"].astype(float) * df["periodo"].map(dolar)

    # a API omite meses sem exportacao: completa a grade UF x mes com zero
    grade = pd.MultiIndex.from_product(
        [df["localidade"].unique(), sorted(df["periodo"].unique())],
        names=["localidade", "periodo"],
    )
    df = df.set_index(["localidade", "periodo"])["valor"].reindex(grade, fill_value=0).reset_index()

    return formatar("setor", "AGRO_EXPORTACAO", df)


def formatar(nivel, segmento, df):
    """Colunas localidade, periodo (AAAAMM), valor -> formato final do dataset."""
    df = df.dropna(subset=["valor"])
    return pd.DataFrame({
        "nivel": nivel,
        "segmento": segmento,
        "uf": df["localidade"].map(UF_SIGLA),
        "ano": df["periodo"].str[:4].astype(int),
        "mes": df["periodo"].str[4:].astype(int),
        "valor": df["valor"].round().astype("int64"),
    })


def main():
    parser = argparse.ArgumentParser(description="Dataset de faturamento mensal por segmento e UF")
    parser.add_argument("--periodos", default="201201-202612", help="intervalo AAAAMM-AAAAMM")
    args = parser.parse_args()

    tarefas = [(c["segmento"], lambda c=c: estimar(c, args.periodos)) for c in SEGMENTOS]
    tarefas.append(("AGRO_EXPORTACAO", lambda: agro_exportacao(args.periodos)))

    partes = []
    for nome, tarefa in tarefas:
        print(f"[{nome}] baixando...", flush=True)
        try:
            df = tarefa()
        except Exception as erro:
            print(f"[{nome}] FALHOU: {erro}", file=sys.stderr)
            continue
        print(f"[{nome}] {df['uf'].nunique()} UFs, {len(df)} linhas")
        partes.append(df)

    if not partes:
        sys.exit("nenhum dado coletado")

    dataset = pd.concat(partes, ignore_index=True)
    dataset = dataset.sort_values(["nivel", "segmento", "uf", "ano", "mes"])

    PASTA_DADOS.mkdir(exist_ok=True)
    caminho = PASTA_DADOS / f"faturamento_uf_mensal_{datetime.now():%Y%m%d}.csv"
    dataset.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
    print(f"salvo: {caminho} ({len(dataset)} linhas)")


if __name__ == "__main__":
    main()
