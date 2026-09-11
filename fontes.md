# Fontes dos dados

Todos os dados vêm do **IBGE**, pela API pública de Agregados (SIDRA), sem
cadastro nem chave. Data de acesso: 11/09/2026.

- API: `https://servicodados.ibge.gov.br/api/v3/agregados`
- Documentação: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3
- Consulta das tabelas no navegador: `https://sidra.ibge.gov.br/tabela/<número>`

## Tabelas usadas

| Tabela | Pesquisa | O que foi usado | Coluna no CSV |
|---|---|---|---|
| [8880](https://sidra.ibge.gov.br/tabela/8880) | PMC — Pesquisa Mensal de Comércio | Número-índice (2022=100) da receita nominal de vendas do comércio varejista, sem ajuste sazonal, por UF e Brasil | `indice_receita` (setor `COMERCIO_VAREJISTA`) |
| [5906](https://sidra.ibge.gov.br/tabela/5906) | PMS — Pesquisa Mensal de Serviços | Número-índice (2022=100) da receita nominal de serviços, sem ajuste sazonal, por UF e Brasil | `indice_receita` (setor `SERVICOS`) |
| [1737](https://sidra.ibge.gov.br/tabela/1737) | IPCA — Índice Nacional de Preços ao Consumidor Amplo | Número-índice (dez/1993=100), Brasil | `ipca` |

Páginas das pesquisas:
- PMC: https://www.ibge.gov.br/estatisticas/economicas/comercio/9227-pesquisa-mensal-de-comercio.html
- PMS: https://www.ibge.gov.br/estatisticas/economicas/servicos/9229-pesquisa-mensal-de-servicos.html

## Consideradas e deixadas de fora

| Fonte | Por que ficou de fora |
|---|---|
| IBGE PIM-PF (indústria, tabela 8888) | mede quantidade produzida, não faturamento |
| Agro: IBGE PAM e PPM, VBP do MAPA, Comex Stat | não existe faturamento mensal do agro por estado; só valores anuais ou só exportação |
| IBGE PMC veículos (8884) e PMS por atividade (8693) | só 12 estados |
| IBGE PAC e PAS (receitas anuais em R$) | anuais, não servem para série mensal |
| Kaggle — Olist e outros | dados de uma empresa só, não do setor |
| CONFAZ — arrecadação de ICMS por setor | é imposto, não faturamento, e muda com alterações de alíquota |

Uma primeira versão do projeto combinava várias dessas fontes para estimar
faturamento em reais de 12 segmentos (disponível no histórico do git, commit
`12e9150`). Foi simplificada para ficar só com os dados mais diretos e fáceis de
explicar.

## Como citar (ABNT)

- IBGE. **Pesquisa Mensal de Comércio**. Rio de Janeiro: IBGE, 2026. Disponível
  em: https://sidra.ibge.gov.br/tabela/8880. Acesso em: 11 set. 2026.
- IBGE. **Pesquisa Mensal de Serviços**. Rio de Janeiro: IBGE, 2026. Disponível
  em: https://sidra.ibge.gov.br/tabela/5906. Acesso em: 11 set. 2026.
- IBGE. **Índice Nacional de Preços ao Consumidor Amplo – IPCA**. Rio de Janeiro:
  IBGE, 2026. Disponível em: https://sidra.ibge.gov.br/tabela/1737. Acesso em: 11
  set. 2026.
