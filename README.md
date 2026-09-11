# Faturamento do varejo e dos serviços por estado

Trabalho da disciplina de Mineração de Dados, seguindo a metodologia
**CRISP-DM**.

## Sobre o projeto

**Pergunta:** em quais estados o faturamento do **comércio varejista** e dos
**serviços** deve crescer acima da inflação nos próximos meses?

**De onde vêm os dados:** todo mês o IBGE publica, para cada estado, um índice
que mostra como está o faturamento do varejo (Pesquisa Mensal de Comércio – PMC)
e dos serviços (Pesquisa Mensal de Serviços – PMS). O projeto baixa esses
índices direto do IBGE, junto com a inflação oficial (IPCA), e monta uma tabela
única:

- **2 setores:** comércio varejista e serviços
- **27 estados + Brasil**
- **mês a mês**, de janeiro/2012 até o último mês publicado

**O que vamos fazer com eles:**

- **K-means** para agrupar estados e setores com comportamento parecido;
- **Random Forest** para prever se o faturamento vai crescer acima da inflação
  nos próximos 3 meses.

O passo a passo do trabalho está em [crisp.md](crisp.md).

## Como gerar os dados

Precisa de internet. A API do IBGE é pública, sem cadastro.

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
[COMERCIO_VAREJISTA] baixando tabela 8880...
[SERVICOS] baixando tabela 5906...
[IPCA] baixando tabela 1737...
salvo: ...\dados\faturamento_uf_mensal_20260911.csv (9772 linhas, 28 localidades)
```

Rodar de novo no futuro já traz os meses mais recentes. Para outro intervalo:
`python dataset.py --periodos 201501-202612`.

## Como o dataset é montado

Tudo acontece no `dataset.py`: são 3 buscas no IBGE e alguns tratamentos simples
até chegar no CSV final.

```
API do IBGE (SIDRA)
 ├─ tabela 8880 — varejo    ─┐
 ├─ tabela 5906 — serviços  ─┼─► organiza em linhas ─► limpa ─► junta o IPCA ─► formata ─► CSV
 └─ tabela 1737 — IPCA      ─┘
```

### De onde vêm os dados

Da **API de Agregados do IBGE**
(`https://servicodados.ibge.gov.br/api/v3/agregados`), que dá acesso por programa
às mesmas tabelas do site [SIDRA](https://sidra.ibge.gov.br). É pública, sem
cadastro nem chave.

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

**4. Juntar o IPCA pelo mês.** O IPCA de cada mês é repetido em todas as linhas
daquele mês — por isso SP, BA e BR têm o mesmo `ipca` em abril/2025 (7276,54).

**5. Formatar.**
- nome do estado → sigla ("São Paulo" → `SP`, "Brasil" → `BR`);
- período → duas colunas ("202504" → `ano` 2025, `mes` 4);
- linhas ordenadas por setor, estado, ano e mês.

**6. Salvar.** `dados/faturamento_uf_mensal_AAAAMMDD.csv`, com separador `;` e
decimal `,` para abrir no Excel em português.

Resultado: varejo com 28 localidades × 174 meses (4.872 linhas) + serviços com
28 × 175 meses (4.900 linhas) = **9.772 linhas**.

### O que fica de fora do dataset (de propósito)

O CSV guarda **exatamente o que o IBGE publica** — todas as colunas são dados
oficiais. As contas abaixo ficam para a etapa de preparação (fase 3 do
[crisp.md](crisp.md)), onde aparecem na análise:

- descontar a inflação (`indice_receita / ipca`);
- calcular a variação contra o mesmo mês do ano anterior;
- tratar o período da pandemia (2020–2021);
- criar os atributos e o alvo do modelo.

## O arquivo gerado

`dados/faturamento_uf_mensal_AAAAMMDD.csv` — abre direto no Excel (separador
`;`, decimal `,`). Uma linha por setor × estado × mês:

```
setor;uf;ano;mes;indice_receita;ipca
COMERCIO_VAREJISTA;SP;2025;3;118,90037;7245,38
COMERCIO_VAREJISTA;SP;2025;4;118,53521;7276,54
```

| Coluna | O que é |
|---|---|
| `setor` | `COMERCIO_VAREJISTA` ou `SERVICOS` |
| `uf` | sigla do estado; `BR` = Brasil |
| `ano`, `mes` | mês de referência |
| `indice_receita` | índice de faturamento do IBGE: **100 = média mensal de 2022**. 118,5 = faturou 18,5% a mais que a média de 2022 |
| `ipca` | índice da inflação oficial, usado para descontar a inflação |

Para ler no Python e descontar a inflação:

```python
import pandas as pd

df = pd.read_csv("dados/faturamento_uf_mensal_20260911.csv", sep=";", decimal=",")
df["indice_real"] = df["indice_receita"] / df["ipca"]
```

Exemplo — varejo de SP, abril/2025 contra abril/2024: faturamento **+13,8%**,
inflação **+5,5%**, crescimento real **+7,8%**.

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
├── dataset.py         # baixa os dados do IBGE e gera o CSV
├── sidra.py           # funções de acesso à API do IBGE
├── explorar.py        # mostra o que uma tabela do IBGE contém (python explorar.py 8880)
├── requirements.txt   # bibliotecas Python
├── README.md          # este arquivo
├── crisp.md           # etapas do CRISP-DM e plano do trabalho
├── guia.md            # termos técnicos explicados
├── fontes.md          # fontes e como citar
├── CLAUDE.md          # contexto técnico e decisões do projeto
└── dados/             # CSV gerado (não vai para o git)
```

## Fontes

IBGE / SIDRA — Pesquisa Mensal de Comércio (tabela 8880), Pesquisa Mensal de
Serviços (tabela 5906) e IPCA (tabela 1737). Links e referências no formato ABNT
em [fontes.md](fontes.md).
