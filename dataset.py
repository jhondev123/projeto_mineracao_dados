"""Monta o dataset de faturamento mensal do comercio varejista e dos servicos
por UF, direto dos indices oficiais do IBGE.

Colunas do CSV (dados/faturamento_uf_mensal_AAAAMMDD.csv):
    setor           COMERCIO_VAREJISTA ou SERVICOS
    uf              sigla do estado; BR = Brasil
    ano, mes        periodo de referencia
    indice_receita  indice de receita nominal (media de 2022 = 100), sem ajuste
                    sazonal. PMC tabela 8880 (varejo) e PMS tabela 5906 (servicos)
    ipca            numero-indice do IPCA (dez/1993 = 100), tabela 1737, Brasil.
                    Desconta a inflacao: indice_real = indice_receita / ipca

Uso:
    python dataset.py
    python dataset.py --periodos 201501-202612
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

import sidra

PASTA_DADOS = Path(__file__).parent / "dados"

# setor: (tabela, variavel "Numero-indice", filtro "indice de receita nominal")
SETORES = {
    "COMERCIO_VAREJISTA": (8880, 7169, "11046[56733]"),
    "SERVICOS": (5906, 7167, "11046[56725]"),
}

# IPCA - numero-indice (dez/1993 = 100)
IPCA_TABELA = 1737
IPCA_VARIAVEL = 2266

UF_SIGLA = {
    "Brasil": "BR",
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR",
    "Pará": "PA", "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA",
    "Piauí": "PI", "Ceará": "CE", "Rio Grande do Norte": "RN", "Paraíba": "PB",
    "Pernambuco": "PE", "Alagoas": "AL", "Sergipe": "SE", "Bahia": "BA",
    "Minas Gerais": "MG", "Espírito Santo": "ES", "Rio de Janeiro": "RJ",
    "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
}


def baixar(tabela, variavel, classificacoes, periodos, localidades):
    """Uma variavel do SIDRA. Colunas: localidade, periodo, valor."""
    payload = sidra.buscar(
        tabela,
        periodos=periodos,
        localidades=localidades,
        classificacoes=classificacoes,
        variaveis=variavel,
    )
    df = pd.DataFrame(sidra.achatar(payload, tabela, ""))
    return df[["localidade", "periodo", "valor"]]


def main():
    parser = argparse.ArgumentParser(description="Dataset de faturamento mensal por setor e UF")
    parser.add_argument("--periodos", default="201201-202612", help="intervalo AAAAMM-AAAAMM")
    args = parser.parse_args()

    partes = []
    for setor, (tabela, variavel, filtro) in SETORES.items():
        print(f"[{setor}] baixando tabela {tabela}...", flush=True)
        df = baixar(tabela, variavel, [filtro], args.periodos, "N1[all]|N3[all]")
        df["setor"] = setor
        partes.append(df)
    dados = pd.concat(partes, ignore_index=True).dropna(subset=["valor"])

    print(f"[IPCA] baixando tabela {IPCA_TABELA}...", flush=True)
    ipca = baixar(IPCA_TABELA, IPCA_VARIAVEL, [], args.periodos, "N1[all]")
    ipca = ipca[["periodo", "valor"]].rename(columns={"valor": "ipca"})
    dados = dados.merge(ipca, on="periodo", how="left")

    saida = pd.DataFrame({
        "setor": dados["setor"],
        "uf": dados["localidade"].map(UF_SIGLA),
        "ano": dados["periodo"].str[:4].astype(int),
        "mes": dados["periodo"].str[4:].astype(int),
        "indice_receita": dados["valor"],
        "ipca": dados["ipca"],
    }).sort_values(["setor", "uf", "ano", "mes"])

    PASTA_DADOS.mkdir(exist_ok=True)
    caminho = PASTA_DADOS / f"faturamento_uf_mensal_{datetime.now():%Y%m%d}.csv"
    saida.to_csv(caminho, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"salvo: {caminho} ({len(saida)} linhas, {saida['uf'].nunique()} localidades)")


if __name__ == "__main__":
    main()
