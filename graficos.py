"""Gera graficos dos dados brutos para explorar e apresentar.

Le o CSV mais recente de dados/ (gerado pelo dataset.py) e salva PNGs em
graficos/.

Uso:
    python graficos.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # so gera os arquivos, nao abre janela

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

from dataset import UF_SIGLA

PASTA = Path(__file__).parent
PASTA_DADOS = PASTA / "dados"
PASTA_GRAFICOS = PASTA / "graficos"

# Paleta clara de referencia: cor so nas marcas (linhas, barras, celulas);
# texto, eixos e grade sempre em tons de cinza.
SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
TEXTO_APAGADO = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
AZUL = "#2a78d6"
LARANJA = "#eb6834"
VERMELHO = "#e34948"
NEUTRO = "#f0efec"

SETORES = {
    "COMERCIO_VAREJISTA": ("Comércio varejista", AZUL),
    "SERVICOS": ("Serviços", LARANJA),
}

NOME_UF = {sigla: nome for nome, sigla in UF_SIGLA.items()}

# Brasil no topo, depois UFs agrupadas por regiao (N, NE, SE, S, CO)
ORDEM_UF = [
    "BR",
    "AC", "AM", "AP", "PA", "RO", "RR", "TO",
    "AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE",
    "ES", "MG", "RJ", "SP",
    "PR", "RS", "SC",
    "DF", "GO", "MS", "MT",
]

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

FONTE_IBGE = "Fonte: IBGE — Pesquisa Mensal de Comércio (tabela 8880), Pesquisa Mensal de Serviços (5906) e IPCA (1737)"


def numero(valor, casas=1, sinal=False):
    """Numero no formato brasileiro: 1.234,5"""
    valor = round(valor, casas) + 0.0  # evita "-0,0"
    texto = f"{valor:{'+' if sinal and valor != 0 else ''},.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def mes_ano(linha):
    return f"{MESES[int(linha['mes']) - 1]}/{int(linha['ano'])}"


def estilo():
    plt.rcParams.update({
        "font.family": ["Segoe UI", "DejaVu Sans"],
        "font.size": 10,
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "axes.edgecolor": EIXO,
        "axes.linewidth": 1,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.titlelocation": "left",
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlecolor": TEXTO,
        "axes.titlepad": 10,
        "axes.labelcolor": TEXTO_SECUNDARIO,
        "grid.color": GRADE,
        "grid.linewidth": 1,
        "grid.linestyle": "-",
        "xtick.color": EIXO,
        "ytick.color": EIXO,
        "xtick.labelcolor": TEXTO_APAGADO,
        "ytick.labelcolor": TEXTO_APAGADO,
        "legend.frameon": False,
        "legend.labelcolor": TEXTO_SECUNDARIO,
        "lines.linewidth": 1.8,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
    })


def carregar():
    arquivos = sorted(PASTA_DADOS.glob("faturamento_uf_mensal_*.csv"))
    if not arquivos:
        sys.exit("nenhum CSV em dados/ - rode python dataset.py antes")

    df = pd.read_csv(arquivos[-1], sep=";", decimal=",", encoding="utf-8-sig")
    df["data"] = pd.to_datetime(
        df[["ano", "mes"]].rename(columns={"ano": "year", "mes": "month"}).assign(day=1)
    )

    # faturamento sem inflacao, na mesma escala do indice: media de 2022 = 100
    df["indice_real"] = df["indice_receita"] / df["ipca"]
    base = df[df["ano"] == 2022].groupby(["setor", "uf"])["indice_real"].mean()
    df = df.merge(base.rename("base_2022").reset_index(), on=["setor", "uf"])
    df["indice_real"] = df["indice_real"] / df["base_2022"] * 100
    return df


def nova_figura(largura, altura, titulo, subtitulo, fonte, **kwargs):
    """Figura com titulo, subtitulo e fonte; o layout reserva espaco para eles."""
    fig, eixos = plt.subplots(figsize=(largura, altura), layout="constrained", **kwargs)
    topo = 0.95 / altura
    rodape = 0.4 / altura
    fig.get_layout_engine().set(rect=(0, rodape, 1, 1 - topo - rodape))
    fig.text(0.012, 1 - 0.25 / altura, titulo, fontsize=15, fontweight="bold", color=TEXTO, va="top")
    fig.text(0.012, 1 - 0.6 / altura, subtitulo, fontsize=10.5, color=TEXTO_SECUNDARIO, va="top")
    fig.text(0.012, 0.15 / altura, fonte, fontsize=8.5, color=TEXTO_APAGADO, va="bottom")
    return fig, eixos


def salvar(fig, nome):
    caminho = PASTA_GRAFICOS / nome
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def eixo_anos(ax, datas):
    """Marca de 2 em 2 anos, so dentro do periodo com dados."""
    anos = range(datas.min().year, datas.max().year + 1, 2)
    ax.set_xticks([pd.Timestamp(ano, 1, 1) for ano in anos], [str(ano) for ano in anos])
    ax.grid(axis="x", visible=False)


def eixo_y_numero(ax, casas=0, sufixo=""):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: numero(v, casas) + sufixo))


def barras_uf(ax, crescimento):
    """Barras horizontais de crescimento (%) por UF, maior no topo, Brasil em cinza."""
    valores = crescimento.sort_values()
    cores = [TEXTO_APAGADO if uf == "BR" else AZUL for uf in valores.index]
    ax.barh(valores.index, valores.values, color=cores, height=0.62)
    ax.axvline(0, color=EIXO, linewidth=1)
    for posicao, valor in enumerate(valores.values):
        positivo = valor >= 0
        ax.annotate(f"{numero(valor, 1, sinal=True)}%", xy=(valor, posicao), xytext=(4 if positivo else -4, 0),
                    textcoords="offset points", ha="left" if positivo else "right", va="center",
                    fontsize=8.5, color=TEXTO_SECUNDARIO)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0, labelcolor=TEXTO_SECUNDARIO)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{numero(v, 0)}%"))
    ax.margins(x=0.18, y=0.01)


def grafico_brasil(df):
    fig, ax = nova_figura(
        11, 5.8,
        "Faturamento no Brasil: varejo e serviços",
        "Índice de receita nominal, sem ajuste sazonal (média de 2022 = 100). Valores com inflação, como o IBGE publica.",
        FONTE_IBGE,
    )
    brasil = df[df["uf"] == "BR"]
    for setor, (nome, cor) in SETORES.items():
        serie = brasil[brasil["setor"] == setor]
        ultimo = serie.iloc[-1]
        rotulo = f"{nome} ({mes_ano(ultimo)}: {numero(ultimo['indice_receita'])})"
        ax.plot(serie["data"], serie["indice_receita"], color=cor, label=rotulo)

    ax.axhline(100, color=EIXO, linewidth=1, zorder=1)
    ax.annotate("média de 2022 = 100", xy=(brasil["data"].min(), 100), xytext=(0, 4),
                textcoords="offset points", fontsize=8.5, color=TEXTO_APAGADO)

    abril_2020 = brasil[(brasil["ano"] == 2020) & (brasil["mes"] == 4)]
    fundo = abril_2020.loc[abril_2020["indice_receita"].idxmin()]
    ax.annotate("pandemia (abr/2020)", xy=(fundo["data"], fundo["indice_receita"]), xytext=(0, -14),
                textcoords="offset points", ha="center", va="top", fontsize=9, color=TEXTO_SECUNDARIO)

    eixo_anos(ax, brasil["data"])
    eixo_y_numero(ax)
    ax.legend(loc="upper left")
    return salvar(fig, "01_brasil_faturamento.png")


def grafico_nominal_real(df):
    fig, eixos = nova_figura(
        12, 5.8,
        "Quanto do crescimento é inflação?",
        "Brasil. Nominal = como o IBGE publica; real = descontada a inflação (IPCA). As duas linhas valem 100 na média de 2022.",
        FONTE_IBGE,
        ncols=2, sharey=True,
    )
    brasil = df[df["uf"] == "BR"]
    for ax, (setor, (nome, _)) in zip(eixos, SETORES.items()):
        serie = brasil[brasil["setor"] == setor]
        ax.plot(serie["data"], serie["indice_receita"], color=TEXTO_APAGADO, label="Nominal (com inflação)")
        ax.plot(serie["data"], serie["indice_real"], color=AZUL, label="Real (sem inflação)")
        ax.axhline(100, color=EIXO, linewidth=1, zorder=1)
        ax.set_title(nome)
        eixo_anos(ax, serie["data"])
        eixo_y_numero(ax)
    eixos[0].legend(loc="upper left")
    return salvar(fig, "02_nominal_vs_real.png")


def grafico_sazonalidade(df):
    brasil = df[(df["uf"] == "BR") & (df["ano"] <= 2025) & (df["ano"] != 2020)].copy()
    media_do_ano = brasil.groupby(["setor", "ano"])["indice_receita"].transform("mean")
    brasil["relativo"] = brasil["indice_receita"] / media_do_ano * 100
    perfil = brasil.groupby(["setor", "mes"])["relativo"].mean()

    fig, ax = nova_figura(
        11, 5.8,
        "Sazonalidade: o mesmo desenho todo ano",
        "Brasil. Faturamento de cada mês comparado à média do próprio ano (100 = mês médio). Média de 2012 a 2025, sem 2020.",
        FONTE_IBGE,
    )
    for setor, (nome, cor) in SETORES.items():
        valores = perfil.loc[setor]
        ax.plot(valores.index, valores.values, color=cor, label=nome, marker="o", markersize=7,
                markeredgecolor=SUPERFICIE, markeredgewidth=1.5)

    ax.axhline(100, color=EIXO, linewidth=1, zorder=1)
    dezembro = perfil.loc[("COMERCIO_VAREJISTA", 12)]
    ax.annotate(f"Natal: dezembro do varejo = {numero(dezembro, 0)}", xy=(12, dezembro), xytext=(-12, 0),
                textcoords="offset points", ha="right", va="center", fontsize=9, color=TEXTO_SECUNDARIO)

    ax.set_xticks(range(1, 13), MESES)
    ax.grid(axis="x", visible=False)
    eixo_y_numero(ax)
    ax.legend(loc="upper left")
    return salvar(fig, "03_sazonalidade.png")


def grafico_crescimento_uf(df, ano=2025):
    periodo = df[df["ano"].isin([ano - 1, ano])]
    anual = periodo.groupby(["setor", "uf", "ano"])["indice_real"].sum().unstack("ano")
    crescimento = (anual[ano] / anual[ano - 1] - 1) * 100

    fig, eixos = nova_figura(
        12, 9.5,
        f"Crescimento real do faturamento em {ano}, por estado",
        f"Soma dos 12 meses de {ano} contra {ano - 1}, descontada a inflação (IPCA). Brasil em cinza.",
        FONTE_IBGE,
        ncols=2,
    )
    for ax, (setor, (nome, _)) in zip(eixos, SETORES.items()):
        barras_uf(ax, crescimento.loc[setor])
        ax.set_title(nome)
    return salvar(fig, f"04_crescimento_real_uf_{ano}.png")


def grafico_mapa_calor(df, limite=15):
    completos = df[df["ano"] <= 2025]
    anual = completos.groupby(["setor", "uf", "ano"])["indice_real"].sum()
    crescimento = (anual.groupby(level=["setor", "uf"]).pct_change() * 100).dropna()
    cores = LinearSegmentedColormap.from_list("divergente", [VERMELHO, NEUTRO, AZUL])

    fig, eixos = nova_figura(
        13, 10,
        "Crescimento real ano a ano, por estado",
        f"Faturamento do ano contra o ano anterior, descontada a inflação (IPCA). Vermelho = caiu, azul = cresceu. Escala limitada a ±{limite}%.",
        FONTE_IBGE,
        ncols=2, sharey=True,
    )
    for ax, (setor, (nome, _)) in zip(eixos, SETORES.items()):
        tabela = crescimento.loc[setor].unstack("ano").reindex(ORDEM_UF)
        malha = ax.pcolormesh(tabela.values, cmap=cores, vmin=-limite, vmax=limite,
                              edgecolors=SUPERFICIE, linewidth=1.5)
        ax.set_xticks([i + 0.5 for i in range(len(tabela.columns))], [str(a) for a in tabela.columns], fontsize=8)
        ax.set_yticks([i + 0.5 for i in range(len(tabela.index))], tabela.index)
        ax.set_title(nome)
        ax.grid(False)
        ax.tick_params(length=0)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_visible(False)
    eixos[0].invert_yaxis()  # eixo compartilhado: inverter uma vez so
    eixos[0].tick_params(axis="y", labelcolor=TEXTO_SECUNDARIO)

    barra = fig.colorbar(malha, ax=eixos, extend="both", shrink=0.5, pad=0.02)
    barra.set_label("crescimento real no ano (%)", color=TEXTO_SECUNDARIO)
    barra.outline.set_visible(False)
    barra.ax.tick_params(length=0)
    barra.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{numero(v, 0, sinal=v != 0)}%"))
    return salvar(fig, "05_mapa_calor_crescimento_real.png")


def grafico_indicadores(df):
    macro = df.drop_duplicates("data").sort_values("data").reset_index(drop=True)
    macro["ipca_12m"] = macro["ipca"].pct_change(12) * 100
    paineis = [
        # "\$" evita que o matplotlib leia "$...$" como formula matematica
        ("dolar", r"Dólar (R\$ por US\$, média do mês)", lambda v: f"R$ {numero(v, 2)}"),
        ("selic", "Selic (% ao ano)", lambda v: f"{numero(v, 2)}%"),
        ("ipca_12m", "Inflação: IPCA acumulado em 12 meses (%)", lambda v: f"{numero(v, 1)}%"),
    ]

    fig, eixos = nova_figura(
        11, 9.5,
        "Indicadores da economia",
        "Brasil, valor de cada mês, cada indicador na sua escala. O IPCA em 12 meses começa em 2013 (precisa de um ano de histórico).",
        "Fonte: Banco Central — SGS, séries 3698 (dólar) e 4189 (Selic); IBGE — IPCA (tabela 1737)",
        nrows=3, sharex=True,
    )
    for ax, (coluna, titulo, formato) in zip(eixos, paineis):
        serie = macro.dropna(subset=[coluna])
        ultimo = serie.iloc[-1]
        ax.plot(serie["data"], serie[coluna], color=AZUL)
        ax.scatter([ultimo["data"]], [ultimo[coluna]], s=45, color=AZUL, edgecolors=SUPERFICIE,
                   linewidths=1.5, zorder=3)
        ax.annotate(f"{formato(ultimo[coluna])} ({mes_ano(ultimo)})", xy=(ultimo["data"], ultimo[coluna]),
                    xytext=(8, 0), textcoords="offset points", va="center", fontsize=9, color=TEXTO_SECUNDARIO)
        ax.set_title(titulo, fontsize=11)
        ax.grid(axis="x", visible=False)
        ax.margins(x=0.12)
        eixo_y_numero(ax)
    eixo_anos(eixos[-1], macro["data"])
    return salvar(fig, "06_indicadores_economia.png")


def grafico_historico_uf(df, uf="PR"):
    estado = df[df["uf"] == uf]
    fig, eixos = nova_figura(
        12, 5.8,
        f"{NOME_UF[uf]}: faturamento do varejo e dos serviços",
        "Índice de faturamento (média de 2022 = 100). À esquerda, como o IBGE publica; à direita, descontada a inflação (IPCA).",
        FONTE_IBGE,
        ncols=2, sharey=True,
    )
    paineis = [("indice_receita", "Nominal (com inflação)"), ("indice_real", "Real (sem inflação)")]
    for ax, (coluna, titulo) in zip(eixos, paineis):
        for setor, (nome, cor) in SETORES.items():
            serie = estado[estado["setor"] == setor]
            ax.plot(serie["data"], serie[coluna], color=cor, label=nome)
        ax.axhline(100, color=EIXO, linewidth=1, zorder=1)
        ax.set_title(titulo)
        eixo_anos(ax, estado["data"])
        eixo_y_numero(ax)
    eixos[0].legend(loc="upper left")
    return salvar(fig, f"07_historico_{uf.lower()}.png")


def grafico_comparativo_ufs(df, ufs=("PR", "BA"), ultimo_ano=2025):
    """Crescimento real ano a ano de dois estados, lado a lado, nos dois setores."""
    periodo = df[df["uf"].isin(ufs) & (df["ano"] <= ultimo_ano)]
    anual = periodo.groupby(["setor", "uf", "ano"])["indice_real"].sum()
    crescimento = (anual.groupby(level=["setor", "uf"]).pct_change() * 100).dropna()
    cores = dict(zip(ufs, (AZUL, LARANJA)))  # slots 1 e 2 da paleta: aqui a cor e o estado
    primeiro, segundo = ufs

    fig, eixos = nova_figura(
        12, 6,
        f"{NOME_UF[primeiro]} × {NOME_UF[segundo]}: crescimento real por ano",
        "Faturamento de cada ano contra o ano anterior, descontada a inflação (IPCA). Cada estado comparado com ele mesmo.",
        FONTE_IBGE,
        ncols=2, sharey=True,
    )
    largura = 0.38
    for ax, (setor, (nome, _)) in zip(eixos, SETORES.items()):
        for i, uf in enumerate(ufs):
            valores = crescimento.loc[(setor, uf)]
            posicoes = [ano + (i - 0.5) * largura for ano in valores.index]
            ax.bar(posicoes, valores.values, width=largura, color=cores[uf], label=NOME_UF[uf],
                   edgecolor=SUPERFICIE, linewidth=1)
        ax.axhline(0, color=EIXO, linewidth=1)
        ax.set_title(nome)
        ax.set_xticks(list(valores.index), [str(ano) for ano in valores.index], fontsize=8)
        ax.grid(axis="x", visible=False)
        eixo_y_numero(ax, sufixo="%")
    eixos[0].legend(loc="lower left")
    return salvar(fig, f"08_comparativo_{primeiro.lower()}_{segundo.lower()}.png")


def grafico_ranking_periodo(df, setor="COMERCIO_VAREJISTA", inicio=(2026, 1), fim=(2026, 6)):
    """Crescimento real por UF num periodo escolhido, contra o mesmo periodo do ano anterior."""
    periodo = df["ano"] * 100 + df["mes"]
    de, ate = inicio[0] * 100 + inicio[1], fim[0] * 100 + fim[1]
    do_setor = df["setor"] == setor
    atual = df[do_setor & periodo.between(de, ate)].groupby("uf")["indice_real"].sum()
    anterior = df[do_setor & periodo.between(de - 100, ate - 100)].groupby("uf")["indice_real"].sum()
    crescimento = ((atual / anterior - 1) * 100).dropna()

    nome = SETORES[setor][0]
    texto_inicio = f"{MESES[inicio[1] - 1]}/{inicio[0]}"
    texto_fim = f"{MESES[fim[1] - 1]}/{fim[0]}"
    fig, ax = nova_figura(
        9, 9.5,
        f"{nome}: crescimento real por estado",
        f"De {texto_inicio} a {texto_fim}, contra o mesmo período do ano anterior, sem inflação (IPCA). Brasil em cinza.",
        FONTE_IBGE,
    )
    barras_uf(ax, crescimento)
    apelido = "varejo" if setor == "COMERCIO_VAREJISTA" else "servicos"
    return salvar(fig, f"09_{apelido}_por_estado_{de}_{ate}.png")


def main():
    estilo()
    df = carregar()
    PASTA_GRAFICOS.mkdir(exist_ok=True)

    graficos = [
        grafico_brasil,
        grafico_nominal_real,
        grafico_sazonalidade,
        grafico_crescimento_uf,
        grafico_mapa_calor,
        grafico_indicadores,
        grafico_historico_uf,
        grafico_comparativo_ufs,
        grafico_ranking_periodo,
    ]
    for grafico in graficos:
        print(f"salvo: {grafico(df)}")


if __name__ == "__main__":
    main()
