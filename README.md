# Faturamento setorial por estado — mineração de dados

Trabalho da disciplina de Mineração de Dados, desenvolvido com a metodologia
**CRISP-DM**.

## Sobre o projeto

**Objetivo:** trazer previsibilidade sobre **quais setores da economia, em quais
estados, tendem a ter bom faturamento nos próximos meses** — um apoio à decisão
para quem precisa antecipar onde a receita vai crescer.

**O desafio dos dados:** nenhum órgão oficial publica o faturamento mensal dos
setores em reais por estado. O que existe é espalhado:

- o IBGE publica **índices mensais** de receita (comércio e serviços) e de
  produção (indústria), que mostram o movimento, mas não o valor em R$;
- o IBGE publica **receitas anuais em R$** por estado, que mostram o tamanho, mas
  saem uma vez por ano;
- para o agro, só a **exportação** tem valor mensal por estado (Comex Stat).

**O que este repositório faz:** junta essas fontes oficiais num único dataset
com o **faturamento mensal estimado em R$ por segmento e estado**, de jan/2012 a
2026, pronto para análise e modelagem.

| Segmento | Estados |
|---|---|
| Comércio varejista | 27 |
| Comércio de veículos | 12 |
| Serviços (total e 5 grupos) | 27 (grupos: 12) |
| Indústria (total, extrativa e transformação) | 17 |
| Exportação do agro | 27 |

**Próximas etapas:** análise exploratória e modelagem — K-means para agrupar
setores/estados com comportamento parecido e Random Forest para prever quais vão
crescer acima da inflação nos próximos 3 meses. O plano completo está em
[crisp.md](crisp.md).

## Como gerar os dados

Todas as fontes são APIs públicas, sem cadastro nem chave. É preciso ter
internet.

### 1. Pré-requisitos

- **Python 3.12** — confira com `python --version`. Para instalar no Windows:
  `winget install -e --id Python.Python.3.12`, ou baixe em
  https://www.python.org/downloads/ marcando **"Add python.exe to PATH"**.
- **Git** (para clonar o repositório).

### 2. Instalação

```powershell
git clone https://github.com/jhondev123/projeto_mineracao_dados.git
cd projeto_mineracao_dados
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux/macOS, troque a ativação por `source .venv/bin/activate`.

> Se o PowerShell bloquear o `activate`, dá para rodar sem ativar:
> `.venv\Scripts\python dataset.py`.

### 3. Gerar o dataset

```powershell
python dataset.py
```

O arquivo sai em `dados/faturamento_uf_mensal_AAAAMMDD.csv` (data do dia no
nome). Pode levar alguns minutos. Durante a execução aparece o progresso de cada
segmento:

```
[COMERCIO_VAREJISTA] baixando...
[COMERCIO_VAREJISTA] 27 UFs, 4698 linhas
...
[AGRO_EXPORTACAO] 27 UFs, 4752 linhas
salvo: dados\faturamento_uf_mensal_20260911.csv (32955 linhas)
```

Para outro intervalo de meses:

```powershell
python dataset.py --periodos 201501-202612
```

Rodar de novo no futuro já traz os meses mais recentes publicados.

### O que o script faz

1. **Baixa os índices mensais** de receita nominal do IBGE (PMC e PMS) e, na
   indústria, produção física (PIM-PF) × preço ao produtor (IPP).
2. **Baixa a receita anual de 2024 em R$** de cada estado (PAC, PAS e PIA).
3. **Estima o valor mensal em R$** distribuindo a receita anual pelos meses
   conforme o índice:
   `valor_mês = receita_anual_2024 × índice_mês ÷ soma dos índices de 2024`.
   Assim os meses de 2024 somam exatamente o valor oficial e os demais seguem a
   variação do índice.
4. **Baixa a exportação agropecuária mensal** por estado (Comex Stat, em US$) e
   converte para R$ pelo câmbio médio do mês (Banco Central).
5. **Salva tudo num CSV** único.

Detalhes do método e exemplo com números reais em [guia.md](guia.md).

### Dados brutos (opcional)

O `coleta.py` baixa as tabelas originais do IBGE com todas as variáveis, sem
tratamento — útil para conferir os números:

```powershell
python coleta.py                             # últimos 24 meses, Brasil
python coleta.py --periodos -36              # últimos 36 meses
python coleta.py --localidades N3[all]       # por estado
```

Gera um CSV por pesquisa, um consolidado e um `.xlsx` com uma aba por pesquisa.

Para ver o que uma tabela do IBGE tem antes de baixar:

```powershell
python explorar.py 8880
```

## Formato do dataset

Uma linha por segmento × estado × mês. Separador `;` e codificação UTF-8 com BOM,
então abre direto no Excel em português.

```
nivel;segmento;uf;ano;mes;valor
setor;COMERCIO_VAREJISTA;SP;2025;4;89064213991
setor;INDUSTRIA;SP;2025;4;169056815606
setor;SERVICOS;SP;2025;4;142433645451
```

| Coluna | Descrição |
|---|---|
| `nivel` | `setor` (segmentos que não se sobrepõem) ou `subsetor` (abertura de serviços e indústria) |
| `segmento` | ex.: `SERVICOS`, `SERVICOS_TRANSPORTES`, `AGRO_EXPORTACAO` |
| `uf` | sigla do estado |
| `ano`, `mes` | período de referência |
| `valor` | faturamento do mês em reais (inteiro) |

> **Não some linhas de `setor` com `subsetor`** — os subsetores já estão dentro
> do setor. Para o total de um estado, filtre `nivel == "setor"`.

## Limitações

- O valor mensal em R$ é uma **estimativa** (o nível vem da pesquisa anual). As
  **variações percentuais** são as mesmas dos índices oficiais.
- **Indústria:** usa produção física × preço ao produtor nacional como
  aproximação da receita.
- **Agro:** é só a **exportação** de produtos primários (soja em grão, milho,
  café, algodão...), não o faturamento total do setor.
- Valores **nominais** (com inflação); a correção pelo IPCA é o próximo passo.
- Nem todo segmento cobre os 27 estados (tabela acima).

## Estrutura do repositório

```
projeto_mineracao_dados/
├── dataset.py         # gera o dataset unificado
├── coleta.py          # baixa as tabelas brutas do IBGE
├── explorar.py        # mostra variáveis e classificações de uma tabela do IBGE
├── sidra.py           # cliente da API do IBGE
├── requirements.txt   # dependências Python
├── README.md          # este arquivo
├── fontes.md          # de onde vem cada dado e como citar
├── guia.md            # glossário dos termos técnicos
├── crisp.md           # fases do CRISP-DM: o que foi feito e o plano
├── CLAUDE.md          # contexto técnico completo e decisões do projeto
└── dados/             # saída dos scripts (não versionada)
```

## Fontes

- **IBGE / SIDRA** — PMC, PMS, PIM-PF, IPP, PAC, PAS, PIA
- **Comex Stat / MDIC** — exportações por estado
- **Banco Central / SGS** — câmbio médio mensal

Tabelas, links e referências no formato ABNT em [fontes.md](fontes.md).
