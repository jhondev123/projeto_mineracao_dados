# Projeto de mineração de dados — faturamento do varejo e dos serviços por UF

Documento de contexto e de uso. Descreve o objetivo, como rodar, as decisões já
tomadas e o estado atual do projeto.

## Objetivo

Trabalho de faculdade para a matéria de mineração de dados, seguindo a
metodologia **CRISP-DM**.

### Problema de negócio

Prever **em quais estados o faturamento do comércio varejista e dos serviços
deve crescer acima da inflação nos próximos 3 meses**.

### Escopo (decisão de 2026-09-11)

Só **comércio varejista** (PMC) e **serviços** (PMS), por UF, com o índice
oficial de receita nominal do IBGE e o IPCA, mais dólar e Selic do Banco Central
como indicadores do mês (pedido do usuário para as próximas etapas). O usuário pediu para enxugar: a
apresentação precisa ser simples de explicar. Por isso **não** entram:
estimativa em R$, indústria (proxy produção × preço), agro (exportação via
Comex Stat), veículos e subsetores de serviços (só 12 UFs). Essa versão ampliada
existe no histórico do git (commit `12e9150`) se precisar voltar.

### Fases do CRISP-DM

Detalhe e plano de cada fase: [crisp.md](crisp.md). Glossário: [guia.md](guia.md).

1. **Entendimento do negócio** — feito; definição do alvo a confirmar.
2. **Entendimento dos dados** — coleta, conferência e gráficos iniciais
   (`graficos.py`) feitos; falta completar a exploração.
3. **Preparação** — integração feita (`dataset.py`); faltam atributos e alvo.
4. **Modelagem** — não iniciada. Plano: K-means + Random Forest contra baseline
   de persistência.
5. **Avaliação** — não iniciada.
6. **Implantação** — apresentação na matéria.

### O que o professor pede no seminário

Contextualizar o problema; mostrar as bases com **visualizações, gráficos e
tabelas**; explicar como o CRISP-DM está sendo usado e como será usado nas
próximas etapas; e apontar os **desafios** esperados (balanceamento, limpeza e
transformação dos dados, escolha de modelo, disponibilização do conhecimento
gerado).

## Ambiente

- Windows, pasta `C:\Users\jhonattan\Documents\faculdade\projeto_mineracao_dados`
- Python 3.12, venv local em `.venv`
- Dependências: `requests`, `pandas`, `matplotlib`, `openpyxl`
- Repositório: https://github.com/jhondev123/projeto_mineracao_dados (branch `main`)

## Rodar

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python dataset.py
```

O `python` global do Windows não tem as dependências: sem ativar o venv dá
`ModuleNotFoundError: No module named 'pandas'`. Alternativa sem ativar:
`.venv\Scripts\python dataset.py`.

Opções:

```powershell
python dataset.py --periodos 201501-202612   # outro intervalo
python explorar.py 8880                      # variáveis e classificações de uma tabela
python graficos.py                           # 9 gráficos PNG em graficos/ (lê o CSV mais recente)
python planilha_bruta.py                     # dados brutos das APIs em xlsx, uma aba por fonte
```

## Fonte de dados

Faturamento e IPCA do IBGE, API de Agregados (SIDRA v3), sem autenticação:
`https://servicodados.ibge.gov.br/api/v3/agregados`
Documentação: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3

| Setor / coluna | Tabela | Variável | Filtro |
|---|---|---|---|
| `COMERCIO_VAREJISTA` | 8880 (PMC) | 7169 — Número-índice (2022=100) | `11046[56733]` receita nominal |
| `SERVICOS` | 5906 (PMS) | 7167 — Número-índice (2022=100) | `11046[56725]` receita nominal |
| `ipca` | 1737 (IPCA) | 2266 — Número-índice (dez/1993=100) | — (só Brasil) |

Dólar e Selic do Banco Central, SGS, sem autenticação:
`https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial=01/01/2012&dataFinal=01/12/2026`

| Coluna | Série SGS | O que é |
|---|---|---|
| `dolar` | 3698 | câmbio livre, dólar americano (venda), média mensal (R$/US$) |
| `selic` | 4189 | Selic acumulada no mês, anualizada base 252 (% a.a.) |

Série mensal vem datada no dia 1 (`01/04/2025` → `202504`). Séries diárias do
SGS (ex.: 432, meta Selic) só aceitam janela de 10 anos por consulta — por isso
as mensais. O mês corrente pode vir parcial, mas o merge é pelos meses do
faturamento, então não entra.

Os ids ficam no topo de `dataset.py`. Se o IBGE trocar a tabela (acontece quando
muda o ano-base), achar a nova em https://sidra.ibge.gov.br e conferir os ids
com `explorar.py`.

Fontes consideradas e descartadas, e como citar: [fontes.md](fontes.md).

### Formato de chamada

```
GET /agregados/{tabela}/periodos/{periodos}/variaveis/{variavel}
    ?localidades=N1[all]|N3[all]
    &classificacao=11046[56733]
```

- `periodos`: `201201-202612` (intervalo) ou `-24` (últimos 24)
- `localidades`: `N1` = Brasil, `N3` = UFs
- `sidra.buscar` aceita `classificacoes` como ids (todas as categorias) ou
  filtros prontos (`"11046[56733]"`), e `variaveis` como id

### Formato da resposta (v3)

JSON aninhado: variável → resultados (com `classificacoes`) → séries (com
`localidade`) → `serie` `{periodo: valor}`. Valores especiais do SIDRA: `-`
(zero absoluto), `0` (zero arredondado), `X` (sigilo), `..` (não se aplica),
`...` (não disponível). `sidra.converter_valor` transforma todos exceto `0` em
`None`.

## Dataset

Saída: `dados/faturamento_uf_mensal_YYYYMMDD.csv` — separador `;`, decimal `,`,
BOM UTF-8. Uma linha por setor × UF × mês:

```
setor;uf;ano;mes;indice_receita;ipca;dolar;selic
COMERCIO_VAREJISTA;SP;2025;3;118,90037;7245,38;5,7468;13,57
COMERCIO_VAREJISTA;SP;2025;4;118,53521;7276,54;5,7837;14,15
```

- `uf = BR` é o Brasil. IPCA, dólar e Selic são nacionais, iguais para todas as
  UFs.
- `indice_real = indice_receita / ipca` desconta a inflação.
- Ler em pandas: `pd.read_csv(caminho, sep=";", decimal=",")`.

### Por que esse índice

Das variáveis das tabelas, só o **número-índice de receita nominal sem ajuste
sazonal** representa faturamento: volume desconta preços (mede quantidade),
ajuste sazonal apaga o Natal (que é faturamento real) e as variações % são
derivadas do índice.

### Limitações

- Índice, não R$ (o IBGE não publica faturamento mensal em reais).
- Cobertura das pesquisas: empresas formais com 20+ pessoas ocupadas.
- IPCA, dólar e Selic nacionais aplicados a todas as UFs.

## Decisões de design

1. **Só dados oficiais diretos (IBGE e Banco Central)** — nada estimado, nada de
   proxy; fácil de explicar na apresentação.
2. **Formato longo** — uma linha por setor × UF × mês; facilita filtro e pivot.
3. **KISS** — `dataset.py` (orquestra e grava), `sidra.py` (cliente da API),
   `explorar.py` (metadados). Ids fixos no topo do `dataset.py`.
4. **CSV para Excel PT-BR** — `;`, decimal `,`, BOM UTF-8.
5. **Gráficos (`graficos.py`)** — matplotlib, PNG 150 dpi, tema claro com a
   paleta de referência da skill dataviz (azul `#2a78d6` = varejo, laranja
   `#eb6834` = serviços; divergente vermelho ↔ cinza ↔ azul), texto em cinza,
   grade fina contínua, **nunca eixo duplo** (indicadores em painéis separados).
   A deflação (`indice_receita / ipca`, rebase 2022 = 100) é feita só para
   visualizar; o CSV fica cru. Títulos com `$` precisam de `\$` (mathtext). O
   validador de paleta da skill precisa de Node, que não está instalado.
6. **Planilha bruta (`planilha_bruta.py`)** — xlsx para a apresentação mostrar o
   dado como coletado, antes do tratamento (o usuário vai mostrar depois a
   planilha dos dados normalizados). Uma aba por fonte + "Leia-me"; JSON do IBGE
   achatado sem renomear valores (nome da UF por extenso, período `AAAAMM`,
   nome completo da variável), BCB com `data`/`valor` originais. Só números
   viram número. Importa `SETORES`, `IPCA_*`, `BCB_SERIES` e `buscar_bcb` do
   `dataset.py` para as duas saídas não divergirem. Sem fórmulas (não há
   LibreOffice para recalcular), fonte Arial.

## Estrutura

```
projeto_mineracao_dados/
├── dataset.py         # baixa PMC, PMS, IPCA, dólar e Selic e gera o CSV
├── graficos.py        # gera 9 gráficos PNG em graficos/
├── planilha_bruta.py  # xlsx com os dados como vieram das APIs (dados/dados_brutos_*.xlsx)
├── sidra.py           # cliente da API: requisição + achatamento do JSON
├── explorar.py        # lista variáveis e classificações de uma tabela
├── requirements.txt
├── README.md          # visão geral e como gerar os dados
├── crisp.md           # fases do CRISP-DM: feito e plano
├── guia.md            # glossário (versão simples, com perguntas da apresentação)
├── fontes.md          # tabelas usadas, descartadas e como citar
├── CLAUDE.md          # este arquivo
├── .gitignore
├── dados/             # saída, CSV ignorado no git (criada pelo script)
└── graficos/          # PNGs, ignorados no git (criada pelo script)
```

## Estado atual

**Validado (2026-09-11):** `dataset.py` gerou 9.772 linhas (2 setores × 27 UFs +
BR). Varejo jan/2012–jun/2026, serviços jan/2012–jul/2026, sem meses faltando,
IPCA em todos os meses. Conferido: varejo SP abr/2025 = 118,53521 (igual ao
SIDRA); abr/25 × abr/24 = +13,8% nominal, IPCA +5,5%, real +7,8%.

**Validado (2026-09-11):** colunas `dolar` e `selic` sem nulos (jan/2012: R$ 1,79
e 10,70%; jul/2026: R$ 5,11 e 14,15%). `graficos.py` gera os 6 PNGs.

**Validado (2026-09-14):** `planilha_bruta.py` gerou `dados_brutos_20260914.xlsx`
com 6 abas: varejo 4.872 linhas, serviços 4.900, IPCA 176, dólar 176, Selic 177
(a API do BCB já devolve set/2026, mês em andamento — no CSV tratado não entra,
porque o merge é pelos meses do faturamento). Nenhum símbolo do IBGE; SP 202504
= 118,53521, igual ao CSV. `dataset.py` continua com 9.772 linhas e sem nulos
após extrair `buscar_bcb`.

**Gráficos para o seminário (2026-09-14):** `graficos.py` ganhou 07 (histórico de
uma UF, nominal × real), 08 (duas UFs, crescimento real anual; aqui a cor é o
estado: azul = 1º, laranja = 2º) e 09 (ranking por UF num período contra o mesmo
período do ano anterior). `barras_uf` é compartilhada entre 04 e 09.

**Apresentação (2026-09-14):** `apresentacao_mineracao_dados.pptx` na raiz, 12
slides (python-pptx; o gerador ficou fora do repo e os números estão fixos no
texto). Cobre os requisitos do professor: problema, bases (tabela + gráficos
nativos de dólar/Selic/IPCA), tratamentos, índice × R$, Paraná, Paraná × Bahia,
CRISP-DM, modelos, API, exemplos e desafios. Números usados, conferidos no CSV:
PR varejo 2025×2024 +2,7% real, 2025×2022 +3,7% real (+18,8% nominal, IPCA
+14,6%); PR serviços 2025×2022 +15,8% real; BA varejo 2012→2025 −6,9% real (PR
+20,2%); 1º sem/2026 varejo: PE +10,4%, TO +5,7%, DF +5,2%, 19 de 27 UFs
positivas. Alvo proposto (3 meses seguintes reais > mesmos meses do ano
anterior): 53,6% positivos no total, mas 6–8% em 2015–16 e 85% em 2022/2024;
~160 meses úteis por série.

**Próximas etapas** (detalhe em [crisp.md](crisp.md)): confirmar definição de
"bom faturamento", completar a exploração, atributos e alvo (variação anual
real, divisão temporal), K-means e Random Forest contra baseline de
persistência.
