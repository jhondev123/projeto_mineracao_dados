"""Cliente minimo da API de Agregados do IBGE (SIDRA v3).

Docs: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3
"""

import requests

BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

# Valores especiais do SIDRA que nao sao numeros.
# -   zero absoluto        ..  nao se aplica
# 0   zero arredondado     ... nao disponivel
# X   valor inibido
NAO_NUMERICOS = {"-", "..", "...", "X"}

TIMEOUT = 60


def _get(url, params=None):
    resposta = requests.get(url, params=params, timeout=TIMEOUT)
    resposta.raise_for_status()
    return resposta.json()


def metadados(tabela):
    """Metadados da tabela: variaveis, classificacoes, periodicidade."""
    return _get(f"{BASE}/{tabela}/metadados")


def ids_classificacoes(meta):
    """Extrai os ids das classificacoes (ex.: tipo de indice, atividade)."""
    return [str(c["id"]) for c in meta.get("classificacoes", [])]


def buscar(tabela, periodos="-24", localidades="N1[all]", classificacoes=None, variaveis="all"):
    """Baixa os dados da tabela.

    periodos: "-24" = ultimos 24 periodos. Tambem aceita "202401-202512".
    localidades: "N1[all]" = Brasil. "N3[all]" = todas as UFs.
    classificacoes: lista de ids (todas as categorias) ou filtros prontos como
        "11046[56733]"; None = descobre sozinho nos metadados.
    variaveis: "all" ou ids separados por "|".
    """
    if classificacoes is None:
        classificacoes = ids_classificacoes(metadados(tabela))

    url = f"{BASE}/{tabela}/periodos/{periodos}/variaveis/{variaveis}"
    params = {"localidades": localidades}
    if classificacoes:
        params["classificacao"] = "|".join(
            c if "[" in str(c) else f"{c}[all]" for c in classificacoes
        )

    return _get(url, params)


def achatar(payload, tabela, pesquisa):
    """Converte o JSON aninhado da API em uma lista de dicts (formato longo).

    Uma linha por variavel x classificacao x localidade x periodo.
    """
    linhas = []

    for variavel in payload:
        nome_variavel = variavel.get("variavel")
        unidade = variavel.get("unidade")

        for resultado in variavel.get("resultados", []):
            classificacoes = {}
            for classificacao in resultado.get("classificacoes", []):
                # "categoria" vem como {id_categoria: nome_categoria}
                nome = classificacao.get("nome")
                categoria = list(classificacao.get("categoria", {}).values())
                classificacoes[nome] = categoria[0] if categoria else None

            for serie in resultado.get("series", []):
                localidade = serie.get("localidade", {}).get("nome")

                for periodo, valor in serie.get("serie", {}).items():
                    linha = {
                        "pesquisa": pesquisa,
                        "tabela": tabela,
                        "periodo": periodo,
                        "localidade": localidade,
                        "variavel": nome_variavel,
                        "unidade": unidade,
                        "valor": converter_valor(valor),
                    }
                    linha.update(classificacoes)
                    linhas.append(linha)

    return linhas


def converter_valor(valor):
    """Transforma o valor em float, ou None se for um simbolo especial."""
    if valor is None or valor in NAO_NUMERICOS:
        return None
    try:
        return float(valor)
    except ValueError:
        return None
