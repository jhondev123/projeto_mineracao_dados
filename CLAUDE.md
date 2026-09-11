# Projeto de mineração de dados — faturamento setorial IBGE/SIDRA

Documento de contexto e de uso. Descreve o objetivo, como rodar, as decisões já
tomadas e o estado atual do projeto.

## Objetivo

Trabalho de faculdade para a matéria de mineração de dados, seguindo a
metodologia **CRISP-DM** (Cross Industry Standard Process for Data Mining).

### Problema de negócio

Trazer **previsibilidade de quais setores da economia brasileira tendem a ter
bom faturamento nos próximos meses** — um apoio à decisão para quem precisa
antecipar tendência de receita por setor (comércio, serviços, indústria e
exportação do agro).

### Fases do CRISP-DM e onde o projeto está

Detalhamento de cada fase, do que já foi feito e do plano: [crisp.md](crisp.md).
Glossário dos termos técnicos: [guia.md](guia.md).

1. **Entendimento do negócio** — feito: prever quais segmentos × UFs terão
   crescimento real de faturamento nos próximos 3 meses. O IBGE não publica
   faturamento mensal em R$; a base são índices de receita nominal (ver decisão
   de escopo abaixo). Definição exata do alvo a confirmar.
2. **Entendimento dos dados** — coleta e verificação de qualidade feitas
   (`explorar.py`, `coleta.py`, `dataset.py`, `fontes.md`); falta a análise
   exploratória.
3. **Preparação dos dados** — integração feita (`dataset.py`, ver seção Dataset
   unificado); falta deflacionar pelo IPCA, criar atributos e alvo.
4. **Modelagem** — não iniciada. Plano: **K-means** para agrupar séries por
   perfil de faturamento e **Random Forest** para classificar crescimento real
   nos próximos 3 meses, comparado a um baseline de persistência.
5. **Avaliação** — não iniciada.
6. **Implantação** — o entregável final é a apresentação na matéria.

Baixa os indicadores direto da API de Agregados do IBGE e salva em CSV e Excel.

## Ambiente

- Windows, pasta `C:\Users\jhonattan\Documents\faculdade\projeto_mineracao_dados`
- Python 3.12, venv local em `.venv`
- Dependências: `requests`, `pandas`, `openpyxl`

### Instalar o Python (Windows)

Confira se já tem:

```powershell
python --version
```

Se não tiver, pelo winget:

```powershell
winget install -e --id Python.Python.3.12
```

Ou baixe em https://www.python.org/downloads/ — na instalação, marque
**"Add python.exe to PATH"**. Feche e reabra o terminal depois.

## Rodar

Na pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python coleta.py
```

Os arquivos saem em `dados/`.

### Opções

```powershell
python coleta.py --periodos -36              # últimos 36 meses
python coleta.py --periodos 202301-202612    # intervalo específico
python coleta.py --localidades N3[all]       # quebra por UF em vez de Brasil
python dataset.py                            # dataset unificado em R$ por segmento x UF
python dataset.py --periodos 201501-202612   # idem, outro intervalo
```

Para inspecionar uma tabela antes de coletar:

```powershell
python explorar.py 8688
```

Isso lista as variáveis e classificações disponíveis. Se algum número de tabela
estiver desatualizado (o IBGE troca as tabelas quando muda o ano-base), procure a
nova em https://sidra.ibge.gov.br/pesquisa/pmc/tabelas e ajuste o dicionário
`TABELAS` no topo de `coleta.py`.

## Fonte de dados

Lista completa de fontes, tabelas, URLs e como citar: [fontes.md](fontes.md).
Além do IBGE, o `dataset.py` usa o Comex Stat (MDIC) e o SGS do Banco Central.

API de Agregados do IBGE (SIDRA v3):
`https://servicodados.ibge.gov.br/api/v3/agregados`
Documentação: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3

Sem autenticação, sem chave de API.

### Tabelas usadas

| Chave no código | Tabela | Conteúdo |
|---|---|---|
| `PMC_varejista` | 8880 | Pesquisa Mensal de Comércio — receita nominal e volume de vendas do varejo, por atividade |
| `PMC_varejista_ampliado` | 8881 | PMC ampliado — inclui veículos, motos, partes e material de construção |
| `PMS_servicos` | 8688 | Pesquisa Mensal de Serviços — receita nominal e volume, por atividade |

### Decisão importante sobre o escopo

O IBGE **não publica faturamento em reais** nessas pesquisas. O indicador de
faturamento é a **receita nominal**, divulgada como número-índice (base 2022=100)
e como variações percentuais (M/M-1, M/M-12, acumulado no ano, acumulado 12 meses).

A **indústria** não tem receita mensal no IBGE, só produção física (PIM-PF,
tabela 8888). No `dataset.py` ela entra por proxy: produção física × índice de
preços ao produtor (IPP), ancorado na receita anual da PIA.

O **agro** não tem receita mensal por UF em nenhuma fonte oficial (PAM, PPM e o
VBP do MAPA são anuais). No `dataset.py` ele entra como **exportação mensal de
produtos agropecuários por UF** (Comex Stat), convertida para R$ — é receita de
exportação, não faturamento total do agro. Detalhes em [fontes.md](fontes.md).

### Formato de chamada

```
GET /agregados/{tabela}/periodos/{periodos}/variaveis/all
    ?localidades=N1[all]
    &classificacao=104[all]|11255[all]
```

- `periodos`: `-24` = últimos 24 períodos; ou intervalo `202401-202512`
- `localidades`: `N1[all]` = Brasil; `N3[all]` = todas as UFs
- `classificacao`: ids descobertos em tempo de execução via `/agregados/{tabela}/metadados`

### Formato da resposta (v3)

JSON aninhado em quatro níveis:

```json
[
  {
    "id": "7169",
    "variavel": "Índice de receita nominal de serviços",
    "unidade": "Número-índice",
    "resultados": [
      {
        "classificacoes": [
          { "id": "11046", "nome": "Setor", "categoria": { "56726": "Serviços prestados às famílias" } }
        ],
        "series": [
          {
            "localidade": { "id": "1", "nivel": { "id": "N1" }, "nome": "Brasil" },
            "serie": { "202506": "132.5", "202507": "-", "202508": "135.10" }
          }
        ]
      }
    ]
  }
]
```

Valores especiais do SIDRA que não são números: `-` (zero absoluto), `0` (zero
arredondado), `X` (inibido por sigilo), `..` (não se aplica), `...` (não
disponível). O código converte todos exceto `0` para `None`.

## Decisões de design

1. **Nada de IDs de variável hardcoded.** O script lê `/metadados` da tabela,
   extrai os ids das classificações e usa `variaveis/all`. Menos configuração e
   não quebra quando o IBGE muda o ano-base (o que já aconteceu: as tabelas
   antigas 6443/6444 foram encerradas em jan/2022 e substituídas).
2. **Formato longo (tidy)** em vez de wide — uma linha por
   variável × classificação × localidade × período. Facilita filtro e pivot
   depois.
3. **KISS**: três arquivos, sem camada de abstração, sem ORM, sem cache. Config
   é um dicionário no topo de `coleta.py`.
4. CSV com separador `;`, decimal `,` e BOM UTF-8 para abrir direto no Excel
   PT-BR; mais um `.xlsx` com uma aba por pesquisa.

## Estrutura

```
projeto_mineracao_dados/
├── sidra.py           # cliente da API: requisição + achatamento do JSON
├── coleta.py          # coleta bruta: todas as variáveis das tabelas, formato longo
├── dataset.py         # dataset unificado: faturamento mensal estimado em R$ por segmento × UF
├── explorar.py        # utilitário: lista variáveis e classificações de uma tabela
├── fontes.md          # de onde vem cada dado (tabelas, URLs, como citar)
├── guia.md            # glossário dos termos técnicos usados no dataset
├── crisp.md           # fases do CRISP-DM: o que foi feito e o plano de cada uma
├── requirements.txt
├── CLAUDE.md           # este arquivo
├── .gitignore
└── dados/             # saída (csv + xlsx), ignorada no git
```

- `sidra.py` — cliente da API (requisição + achatamento do JSON)
- `coleta.py` — script principal, configuração das tabelas e gravação
- `explorar.py` — inspeciona metadados de uma tabela
- `dados/` — saída

## Formato de saída

CSV em formato longo — uma linha por variável × atividade × período:

| pesquisa | tabela | periodo | localidade | variavel | unidade | valor | *(colunas de classificação)* | data |
|---|---|---|---|---|---|---|---|---|

As colunas de classificação são dinâmicas — dependem da tabela. Na PMS aparece
algo como `Atividades` ou `Setor`; na PMC, `Tipos de índice` e `Atividades`.

Separador `;` e decimal `,`, com BOM UTF-8, então abre direto no Excel PT-BR.
O `.xlsx` traz uma aba por pesquisa.

Valores especiais do SIDRA (`-`, `..`, `...`, `X`) viram células vazias.

Arquivos gerados em `dados/`, com carimbo de data no nome:
- um CSV por pesquisa
- `faturamento_setores_YYYYMMDD.csv` (consolidado)
- `faturamento_setores_YYYYMMDD.xlsx` (uma aba por pesquisa)

## Dataset unificado (`dataset.py`)

Saída: `dados/faturamento_uf_mensal_YYYYMMDD.csv` — separador `;`, BOM UTF-8,
valor inteiro em reais. Uma linha por segmento × UF × mês:

```
nivel;segmento;uf;ano;mes;valor
setor;COMERCIO_VAREJISTA;SP;2025;4;89064213991
setor;INDUSTRIA;SP;2025;4;169056815606
setor;SERVICOS;SP;2025;4;142433645451
```

### Qual índice representa faturamento

Das variáveis que a API retorna, só uma interessa: **Número-índice (2022=100),
sem ajuste sazonal, tipo "receita nominal"** (PMC var 7169, PMS var 7167). O
resto é descartado:
- *volume*: receita deflacionada (quantidade vendida), não é faturamento;
- *com ajuste sazonal*: tira a sazonalidade, que faz parte do faturamento real;
- *variações %* (M/M-1, M/M-12, acumulados): derivadas do próprio número-índice.

### Método: índice mensal ancorado na receita anual em R$

```
valor_mes = receita_anual_UF[2024] × indice_mes / soma(indices dos 12 meses de 2024)
```

Os meses de 2024 somam exatamente a receita oficial da pesquisa anual
(PAC/PAS/PIA, em mil reais × 1000); os demais meses seguem o índice mensal. É
uma **estimativa** — o IBGE não publica faturamento mensal em R$. `ANO_BASE`
fica no topo de `dataset.py`; trocar quando sair PAC/PAS/PIA de ano mais novo.

### Segmentos

| nivel | segmento | índice mensal | receita anual (R$) | UFs |
|---|---|---|---|---|
| setor | COMERCIO_VAREJISTA | PMC 8880 | PAC 10653 "4. Comércio varejista" (receita bruta de revenda) | 27 |
| setor | COMERCIO_VEICULOS | PMC 8884 | PAC 10653 "2. Veículos e motocicletas" | 12 |
| setor | SERVICOS | PMS 5906 | PAS 10762 Total (receita bruta de serviços) | 27 |
| setor | INDUSTRIA | PIM-PF 8888 × IPP 6903 | PIA 10457 Total (receitas líquidas de vendas) | 17 |
| setor | AGRO_EXPORTACAO | Comex Stat: exportação ISIC Seção A, US$ FOB × câmbio médio BCB (SGS 3698) | — (já é valor mensal) | 27 |
| subsetor | SERVICOS_FAMILIAS, _INFORMACAO_COMUNICACAO, _PROFISSIONAIS_ADMINISTRATIVOS, _TRANSPORTES, _OUTROS | PMS 8693 | PAS 10762 por grupo | 12 |
| subsetor | INDUSTRIA_EXTRATIVA, INDUSTRIA_TRANSFORMACAO | PIM-PF 8888 × IPP 6903 | PIA 10457 seções B e C | 11 / 17 |

- **Não somar `setor` com `subsetor`**: subsetores são a abertura de SERVICOS e
  INDUSTRIA. Filtrando `nivel == "setor"` os segmentos não se sobrepõem.
- Série começa em jan/2012, exceto INDUSTRIA (dez/2013, início do IPP "indústria
  geral") e MA/MS/RN na indústria e SP na extrativa (jan/2022, quando entraram na
  PIM regional).
- Serviços por grupo (8693): BA, CE, DF, ES, GO, MG, PE, PR, RJ, RS, SC, SP.
  Indústria: AM, BA, CE, ES, GO, MA, MG, MS, MT, PA, PE, PR, RJ, RN, RS, SC, SP.

### Limitações (deixar explícito no relatório)

- Indústria não tem índice de receita mensal: o proxy é produção física por UF ×
  preço ao produtor **nacional** (o IPP não tem quebra por UF).
- COMERCIO_VAREJISTA: o índice é o varejo restrito (sem material de construção),
  mas a âncora da PAC inclui material de construção — nível levemente
  superestimado, tendência preservada.
- SERVICOS_OUTROS: PMS "5. Outros" ≈ PAS imobiliárias + manutenção + outras (não
  bate 1:1).
- Fora de 2024, setor e soma dos subsetores divergem até ~4% (serviços) e ~10%
  (indústria), porque cada índice evolui por conta própria.
- Atacado de alimentos (PMC 8190) ficou de fora: a PAC não publica o grupo na
  maioria das UFs. Turismo (PMS 8694) ficou de fora por se sobrepor a serviços.
- Extrativa em UFs pequenas (MA, RN, MS) é muito volátil mês a mês.
- AGRO_EXPORTACAO não usa o método de âncora: é o valor exportado no mês, em R$.
  Só produtos primários (ISIC A: soja em grão, milho, café verde, algodão...);
  carne, açúcar e farelo estão na indústria de transformação. Meses sem
  exportação entram como 0 (AP, SE, RR, DF, TO, AC, PI). A série oscila também
  com o câmbio.

## Estado atual e pontos em aberto

**Validado (2026-09-11):** a coleta foi testada de ponta a ponta contra a API
real do IBGE — `explorar.py 8688` e `coleta.py --periodos -3` rodaram sem erro
e geraram CSV/XLSX corretos nas três tabelas (`PMC_varejista`,
`PMC_varejista_ampliado`, `PMS_servicos`).

**Validado (2026-09-11):** `dataset.py` gerou 32.955 linhas (12 segmentos,
jan/2012 a ago/2026). Conferido: soma de 2024 = receita anual oficial (ex.:
varejo SP R$ 1.021,6 bi); soma dos subsetores = setor em 2024; sem buracos nas
séries; saltos grandes batem com eventos reais (pandemia 2020, enchente RS
mai/2024). Agro: R$ 432 bi em 2025 no Brasil, MT lidera (R$ 118 bi), pico de
mar–jul (soja).

**Próximas etapas** (detalhe em [crisp.md](crisp.md)): confirmar a definição de
"bom faturamento", análise exploratória, deflacionar pelo IPCA (IBGE tabela
1737, variável 2266), criar atributos e alvo, e modelar (K-means + Random Forest
contra baseline de persistência, com divisão temporal treino/validação/teste).
