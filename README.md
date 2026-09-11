# Faturamento do varejo e dos serviços por estado

Trabalho da disciplina de Mineração de Dados, seguindo a metodologia
**CRISP-DM**.

## Sobre o projeto

**Pergunta:** em quais estados o faturamento do **comércio varejista** e dos
**serviços** deve crescer acima da inflação nos próximos meses?

**De onde vêm os dados:** todo mês o IBGE publica, para cada estado, um índice
que mostra como está o faturamento do varejo (Pesquisa Mensal de Comércio – PMC)
e dos serviços (Pesquisa Mensal de Serviços – PMS). O projeto baixa esses
índices direto do IBGE, junto com a inflação oficial (IPCA) e, do Banco Central,
o dólar e a taxa Selic, e monta uma tabela única:

- **2 setores:** comércio varejista e serviços
- **27 estados + Brasil**
- **mês a mês**, de janeiro/2012 até o último mês publicado

**O que vamos fazer com eles:**

- **K-means** para agrupar estados e setores com comportamento parecido;
- **Random Forest** para prever se o faturamento vai crescer acima da inflação
  nos próximos 3 meses.

O passo a passo do trabalho está em [crisp.md](crisp.md).

## Como gerar os dados

Precisa de internet. As APIs do IBGE e do Banco Central são públicas, sem
cadastro.

### 1. Instalar o Python

Confira se já tem o **Python 3.12** com `python --version`. Se não tiver:
`winget install -e --id Python.Python.3.12`, ou baixe em
https://www.python.org/downloads/ marcando **"Add python.exe to PATH"**.

### 2. Preparar o projeto (só na primeira vez)

```powershell
git clone https://github.com/jhondev123/projeto_mineracao_dados.git
cd projeto_mineracao_dados
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux/macOS, a ativação é `source .venv/bin/activate`.

### 3. Gerar o dataset

Toda vez que abrir um terminal novo, ative o ambiente antes:

```powershell
.venv\Scripts\activate
python dataset.py
```

> **Deu `ModuleNotFoundError: No module named 'pandas'`?** O ambiente não está
> ativado. Rode `.venv\Scripts\activate` (aparece `(.venv)` no início da linha)
> ou chame direto `.venv\Scripts\python dataset.py`.

Saída esperada:

```
[COMERCIO_VAREJISTA] baixando tabela 8880 do IBGE...
[SERVICOS] baixando tabela 5906 do IBGE...
[IPCA] baixando tabela 1737 do IBGE...
[DOLAR] baixando serie 3698 do Banco Central...
[SELIC] baixando serie 4189 do Banco Central...
salvo: ...\dados\faturamento_uf_mensal_20260911.csv (9772 linhas, 28 localidades)
```

Rodar de novo no futuro já traz os meses mais recentes. Para outro intervalo:
`python dataset.py --periodos 201501-202612`.

## Como o dataset é montado

Tudo acontece no `dataset.py`: são 3 buscas no IBGE, 2 no Banco Central e alguns
tratamentos simples até chegar no CSV final.

```
IBGE (SIDRA)                         Banco Central (SGS)
 ├─ tabela 8880 — varejo              ├─ série 3698 — dólar
 ├─ tabela 5906 — serviços            └─ série 4189 — Selic
 └─ tabela 1737 — IPCA                        │
        │                                     │
        ▼                                     ▼
 organiza em linhas ─► limpa ─► junta IPCA, dólar e Selic pelo mês ─► formata ─► CSV
```

### De onde vêm os dados

- **Faturamento e inflação:** da **API de Agregados do IBGE**
  (`https://servicodados.ibge.gov.br/api/v3/agregados`), que dá acesso por
  programa às mesmas tabelas do site [SIDRA](https://sidra.ibge.gov.br).
- **Dólar e Selic:** da API do **SGS do Banco Central**
  (`https://api.bcb.gov.br/dados/serie/bcdata.sgs.<série>/dados`), o sistema de
  séries históricas do BCB.

As duas são públicas, sem cadastro nem chave.

### Quais dados buscamos

Cada tabela do IBGE traz várias versões do mesmo dado (com e sem ajuste
sazonal, variações %, volume...). O script pede **só a versão que representa o
faturamento**, já filtrada na chamada:

| Tabela | Pesquisa | O que a tabela oferece | O que pegamos | Recorte |
|---|---|---|---|---|
| [8880](https://sidra.ibge.gov.br/tabela/8880) | PMC — Pesquisa Mensal de Comércio | 6 variáveis × 2 tipos (receita nominal e volume) | índice de **receita nominal** (2022 = 100), sem ajuste sazonal | Brasil + 27 UFs |
| [5906](https://sidra.ibge.gov.br/tabela/5906) | PMS — Pesquisa Mensal de Serviços | 6 variáveis × 2 tipos (receita nominal e volume) | índice de **receita nominal** (2022 = 100), sem ajuste sazonal | Brasil + 27 UFs |
| [1737](https://sidra.ibge.gov.br/tabela/1737) | IPCA — inflação oficial | 6 variáveis (índice, variação mensal, acumulados) | **número-índice** do IPCA | só Brasil (não existe por UF) |

Por que só essa versão está explicado em [guia.md](guia.md#5-o-que-o-ibge-oferece-e-o-que-usamos).

Do **Banco Central**, duas séries mensais:

| Série | O que é | Recorte |
|---|---|---|
| 3698 | dólar: quantos reais custa 1 US$ (venda), média do mês | Brasil |
| 4189 | Selic do mês, em % ao ano | Brasil |

Exemplo da chamada feita para o varejo:

```
GET https://servicodados.ibge.gov.br/api/v3/agregados/8880/periodos/201201-202612/variaveis/7169
    ?localidades=N1[all]|N3[all]
    &classificacao=11046[56733]
```

- `7169` = número-índice; `11046[56733]` = tipo "receita nominal"
- `N1` = Brasil; `N3` = estados
- o período vai até dez/2026, mas a API devolve só os meses já publicados

### Tratamentos, passo a passo

**1. Organizar em linhas.** A API devolve os dados aninhados (variável →
localidade → meses). Trecho real da resposta:

```json
"localidade": { "id": "35", "nome": "São Paulo" },
"serie": { "202503": "118.90037", "202504": "118.53521" }
```

O script transforma isso em uma linha por localidade × mês:

| localidade | periodo | valor |
|---|---|---|
| São Paulo | 202503 | 118.90037 |
| São Paulo | 202504 | 118.53521 |

**2. Converter e limpar.** O IBGE manda os números como texto; o script converte
para número. Quando o IBGE não tem o valor, ele manda um símbolo (`X` = sigilo,
`..` = não se aplica, `...` = não disponível, `-` = zero); essas linhas são
descartadas. Na coleta atual nenhum mês ficou faltando.

**3. Marcar o setor e juntar.** Cada linha recebe `COMERCIO_VAREJISTA` ou
`SERVICOS`, e as duas tabelas viram uma só.

**4. Juntar IPCA, dólar e Selic pelo mês.** O Banco Central manda cada série
como uma lista simples (`{"data": "01/04/2025", "valor": "5.7837"}`), e a data
vira o período `202504`. Os três indicadores são nacionais, então o valor do mês
é repetido em todas as linhas daquele mês — por isso SP, BA e BR têm o mesmo
`ipca` (7276,54), `dolar` (5,7837) e `selic` (14,15) em abril/2025.

**5. Formatar.**
- nome do estado → sigla ("São Paulo" → `SP`, "Brasil" → `BR`);
- período → duas colunas ("202504" → `ano` 2025, `mes` 4);
- linhas ordenadas por setor, estado, ano e mês.

**6. Salvar.** `dados/faturamento_uf_mensal_AAAAMMDD.csv`, com separador `;` e
decimal `,` para abrir no Excel em português.

Resultado: varejo com 28 localidades × 174 meses (4.872 linhas) + serviços com
28 × 175 meses (4.900 linhas) = **9.772 linhas**.

### O que fica de fora do dataset (de propósito)

O CSV guarda **exatamente o que o IBGE e o Banco Central publicam** — todas as
colunas são dados oficiais. As contas abaixo ficam para a etapa de preparação (fase 3 do
[crisp.md](crisp.md)), onde aparecem na análise:

- descontar a inflação (`indice_receita / ipca`);
- calcular a variação contra o mesmo mês do ano anterior;
- tratar o período da pandemia (2020–2021);
- criar os atributos e o alvo do modelo.

## O arquivo gerado

`dados/faturamento_uf_mensal_AAAAMMDD.csv` — abre direto no Excel (separador
`;`, decimal `,`). Uma linha por setor × estado × mês:

```
setor;uf;ano;mes;indice_receita;ipca;dolar;selic
COMERCIO_VAREJISTA;SP;2025;3;118,90037;7245,38;5,7468;13,57
COMERCIO_VAREJISTA;SP;2025;4;118,53521;7276,54;5,7837;14,15
```

| Coluna | O que é |
|---|---|
| `setor` | `COMERCIO_VAREJISTA` ou `SERVICOS` |
| `uf` | sigla do estado; `BR` = Brasil |
| `ano`, `mes` | mês de referência |
| `indice_receita` | índice de faturamento do IBGE: **100 = média mensal de 2022**. 118,5 = faturou 18,5% a mais que a média de 2022 |
| `ipca` | índice da inflação oficial, usado para descontar a inflação |
| `dolar` | dólar do mês: quantos reais custa 1 US$ (média) |
| `selic` | taxa Selic do mês, em % ao ano |

Para ler no Python e descontar a inflação:

```python
import pandas as pd

df = pd.read_csv("dados/faturamento_uf_mensal_20260911.csv", sep=";", decimal=",")
df["indice_real"] = df["indice_receita"] / df["ipca"]
```

Exemplo — varejo de SP, abril/2025 contra abril/2024: faturamento **+13,8%**,
inflação **+5,5%**, crescimento real **+7,8%**.

## Gráficos

Com o CSV gerado, rode:

```powershell
python graficos.py
```

Os gráficos saem em `graficos/`, em PNG, prontos para usar em slides:

| Arquivo | O que mostra |
|---|---|
| `01_brasil_faturamento.png` | faturamento do Brasil nos dois setores desde 2012: tendência, picos de Natal e a queda da pandemia |
| `02_nominal_vs_real.png` | a mesma série com e sem inflação: quanto do crescimento é só aumento de preços |
| `03_sazonalidade.png` | o desenho médio do ano: fevereiro fraco, dezembro forte |
| `04_crescimento_real_uf_2025.png` | ranking dos estados pelo crescimento real em 2025 |
| `05_mapa_calor_crescimento_real.png` | crescimento real de cada estado, ano a ano (as crises de 2015–16 e 2020 aparecem em vermelho) |
| `06_indicadores_economia.png` | dólar, Selic e inflação acumulada em 12 meses |

Nos gráficos 02, 04 e 05 a inflação é descontada só para visualizar
(`indice_receita / ipca`); o CSV continua com os dados do jeito que foram
publicados.

## Limitações

- É um **índice**, não valor em reais: mostra quanto o faturamento subiu ou caiu,
  não quanto foi em R$.
- As pesquisas cobrem **empresas formais com 20 ou mais pessoas ocupadas**;
  pequenos negócios e informais ficam de fora.
- Só **varejo e serviços**: são os setores em que o IBGE publica faturamento
  mensal por estado.

Os termos técnicos estão explicados em [guia.md](guia.md).

## Estrutura

```
projeto_mineracao_dados/
├── dataset.py         # baixa os dados do IBGE e do Banco Central e gera o CSV
├── graficos.py        # gera os gráficos PNG a partir do CSV
├── sidra.py           # funções de acesso à API do IBGE
├── explorar.py        # mostra o que uma tabela do IBGE contém (python explorar.py 8880)
├── requirements.txt   # bibliotecas Python
├── README.md          # este arquivo
├── crisp.md           # etapas do CRISP-DM e plano do trabalho
├── guia.md            # termos técnicos explicados
├── fontes.md          # fontes e como citar
├── CLAUDE.md          # contexto técnico e decisões do projeto
├── dados/             # CSV gerado (não vai para o git)
└── graficos/          # PNGs gerados (não vão para o git)
```

## Fontes

- **IBGE / SIDRA** — Pesquisa Mensal de Comércio (tabela 8880), Pesquisa Mensal
  de Serviços (tabela 5906) e IPCA (tabela 1737)
- **Banco Central / SGS** — dólar (série 3698) e Selic (série 4189)

Links e referências no formato ABNT em [fontes.md](fontes.md).
