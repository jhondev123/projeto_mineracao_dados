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
oficial de receita nominal do IBGE e o IPCA. O usuário pediu para enxugar: a
apresentação precisa ser simples de explicar. Por isso **não** entram:
estimativa em R$, indústria (proxy produção × preço), agro (exportação via
Comex Stat), veículos e subsetores de serviços (só 12 UFs). Essa versão ampliada
existe no histórico do git (commit `12e9150`) se precisar voltar.

### Fases do CRISP-DM

Detalhe e plano de cada fase: [crisp.md](crisp.md). Glossário: [guia.md](guia.md).

1. **Entendimento do negócio** — feito; definição do alvo a confirmar.
2. **Entendimento dos dados** — coleta e conferência feitas; falta exploração.
3. **Preparação** — integração feita (`dataset.py`); faltam atributos e alvo.
4. **Modelagem** — não iniciada. Plano: K-means + Random Forest contra baseline
   de persistência.
5. **Avaliação** — não iniciada.
6. **Implantação** — apresentação na matéria.

## Ambiente

- Windows, pasta `C:\Users\jhonattan\Documents\faculdade\projeto_mineracao_dados`
- Python 3.12, venv local em `.venv`
- Dependências: `requests`, `pandas`
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
```

## Fonte de dados

Tudo do IBGE, API de Agregados (SIDRA v3), sem autenticação:
`https://servicodados.ibge.gov.br/api/v3/agregados`
Documentação: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3

| Setor / coluna | Tabela | Variável | Filtro |
|---|---|---|---|
| `COMERCIO_VAREJISTA` | 8880 (PMC) | 7169 — Número-índice (2022=100) | `11046[56733]` receita nominal |
| `SERVICOS` | 5906 (PMS) | 7167 — Número-índice (2022=100) | `11046[56725]` receita nominal |
| `ipca` | 1737 (IPCA) | 2266 — Número-índice (dez/1993=100) | — (só Brasil) |

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
setor;uf;ano;mes;indice_receita;ipca
COMERCIO_VAREJISTA;SP;2025;3;118,90037;7245,38
COMERCIO_VAREJISTA;SP;2025;4;118,53521;7276,54
```

- `uf = BR` é o Brasil. O IPCA é nacional, igual para todas as UFs.
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
- IPCA nacional aplicado a todas as UFs.

## Decisões de design

1. **Só IBGE, só dados diretos** — nada estimado, nada de proxy; fácil de
   explicar na apresentação.
2. **Formato longo** — uma linha por setor × UF × mês; facilita filtro e pivot.
3. **KISS** — `dataset.py` (orquestra e grava), `sidra.py` (cliente da API),
   `explorar.py` (metadados). Ids fixos no topo do `dataset.py`.
4. **CSV para Excel PT-BR** — `;`, decimal `,`, BOM UTF-8.

## Estrutura

```
projeto_mineracao_dados/
├── dataset.py         # baixa PMC, PMS e IPCA e gera o CSV
├── sidra.py           # cliente da API: requisição + achatamento do JSON
├── explorar.py        # lista variáveis e classificações de uma tabela
├── requirements.txt
├── README.md          # visão geral e como gerar os dados
├── crisp.md           # fases do CRISP-DM: feito e plano
├── guia.md            # glossário (versão simples, com perguntas da apresentação)
├── fontes.md          # tabelas usadas, descartadas e como citar
├── CLAUDE.md          # este arquivo
├── .gitignore
└── dados/             # saída, CSV ignorado no git (criada pelo script)
```

## Estado atual

**Validado (2026-09-11):** `dataset.py` gerou 9.772 linhas (2 setores × 27 UFs +
BR). Varejo jan/2012–jun/2026, serviços jan/2012–jul/2026, sem meses faltando,
IPCA em todos os meses. Conferido: varejo SP abr/2025 = 118,53521 (igual ao
SIDRA); abr/25 × abr/24 = +13,8% nominal, IPCA +5,5%, real +7,8%.

**Próximas etapas** (detalhe em [crisp.md](crisp.md)): confirmar definição de
"bom faturamento", notebook de exploração, atributos e alvo (variação anual
real, divisão temporal), K-means e Random Forest contra baseline de
persistência.
