"""Coleta os indicadores mensais de faturamento por setor no IBGE/SIDRA
e salva em CSV + Excel na pasta dados/.

Uso:
    python coleta.py              # ultimos 24 meses, Brasil
    python coleta.py --periodos -36 --localidades N3[all]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

import sidra

PASTA_DADOS = Path(__file__).parent / "dados"

# Tabelas do SIDRA com os indicadores de receita/faturamento por setor.
# A receita nominal e o indicador que mede faturamento em valor corrente.
TABELAS = {
    "PMC_varejista": {
        "tabela": 8880,
        "descricao": "Comercio varejista - receita nominal e volume de vendas",
    },
    "PMC_varejista_ampliado": {
        "tabela": 8881,
        "descricao": "Comercio varejista ampliado (inclui veiculos e construcao)",
    },
    "PMS_servicos": {
        "tabela": 8688,
        "descricao": "Servicos - receita nominal e volume, por atividade",
    },
}


def coletar(periodos, localidades):
    frames = {}

    for nome, config in TABELAS.items():
        tabela = config["tabela"]
        print(f"[{nome}] baixando tabela {tabela}...", flush=True)

        try:
            payload = sidra.buscar(tabela, periodos=periodos, localidades=localidades)
        except Exception as erro:
            print(f"[{nome}] FALHOU: {erro}", file=sys.stderr)
            continue

        linhas = sidra.achatar(payload, tabela, nome)
        if not linhas:
            print(f"[{nome}] nenhum registro retornado", file=sys.stderr)
            continue

        df = pd.DataFrame(linhas)
        df["data"] = pd.to_datetime(df["periodo"], format="%Y%m", errors="coerce")
        df = df.sort_values(["variavel", "data"]).reset_index(drop=True)

        frames[nome] = df
        print(f"[{nome}] {len(df)} registros")

    return frames


def salvar(frames):
    PASTA_DADOS.mkdir(exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d")

    for nome, df in frames.items():
        caminho = PASTA_DADOS / f"{nome}_{carimbo}.csv"
        df.to_csv(caminho, index=False, sep=";", decimal=",", encoding="utf-8-sig")
        print(f"salvo: {caminho}")

    if not frames:
        return

    consolidado = pd.concat(frames.values(), ignore_index=True)
    caminho_csv = PASTA_DADOS / f"faturamento_setores_{carimbo}.csv"
    consolidado.to_csv(caminho_csv, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"salvo: {caminho_csv}")

    caminho_xlsx = PASTA_DADOS / f"faturamento_setores_{carimbo}.xlsx"
    with pd.ExcelWriter(caminho_xlsx, engine="openpyxl") as escritor:
        for nome, df in frames.items():
            df.to_excel(escritor, sheet_name=nome[:31], index=False)
    print(f"salvo: {caminho_xlsx}")


def main():
    parser = argparse.ArgumentParser(description="Coleta dados do SIDRA/IBGE")
    parser.add_argument(
        "--periodos",
        default="-24",
        help="-24 = ultimos 24 meses; ou intervalo como 202401-202512",
    )
    parser.add_argument(
        "--localidades",
        default="N1[all]",
        help="N1[all] = Brasil; N3[all] = todas as UFs",
    )
    args = parser.parse_args()

    frames = coletar(args.periodos, args.localidades)
    salvar(frames)

    if not frames:
        sys.exit("nenhum dado coletado")


if __name__ == "__main__":
    main()
