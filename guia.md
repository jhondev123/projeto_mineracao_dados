# Guia de termos

Os conceitos necessários para entender e apresentar os dados do projeto.
Fontes: [fontes.md](fontes.md). Etapas do trabalho: [crisp.md](crisp.md).

---

## 1. De onde vêm os dados

**IBGE** — Instituto Brasileiro de Geografia e Estatística, o órgão oficial de
estatísticas do país.

**SIDRA** — o banco de tabelas do IBGE (sidra.ibge.gov.br). O projeto acessa
esse banco pela **API** do IBGE: o programa pede os dados por um endereço de
internet e recebe a tabela pronta.

**PMC — Pesquisa Mensal de Comércio** — acompanha todo mês o faturamento do
**comércio varejista**: supermercados, combustíveis, roupas e calçados, móveis e
eletrodomésticos, farmácias, livrarias, informática e outros.

**PMS — Pesquisa Mensal de Serviços** — acompanha todo mês o faturamento dos
**serviços** prestados a famílias e empresas: alimentação e hospedagem,
transportes, telecomunicações e informática, serviços profissionais e
administrativos, entre outros.

As duas pesquisam **empresas formais com 20 ou mais pessoas ocupadas**.

**IPCA** — Índice Nacional de Preços ao Consumidor Amplo, a **inflação oficial**
do Brasil, também medida pelo IBGE.

**IPCA acumulado em 12 meses** — quanto os preços subiram nos últimos 12 meses.
É o número de inflação que aparece no noticiário (ex.: "inflação de 4,4% em 12
meses").

**Banco Central (BCB)** — órgão que cuida da moeda e dos juros do país. Publica
suas estatísticas no **SGS** (Sistema Gerenciador de Séries Temporais), que
também tem API pública.

**Dólar** — quantos reais custa um dólar americano. Usamos a **média do mês**
(cotação de venda). Dólar alto encarece importados e combustíveis, o que mexe
nos preços e no consumo.

**Selic** — a taxa básica de juros da economia, definida pelo Banco Central.
Usamos a Selic de cada mês em **% ao ano**. Juros altos encarecem o crédito e o
parcelamento, o que costuma frear as vendas; juros baixos estimulam.

## 2. Número-índice

O IBGE não divulga o faturamento mensal em reais: a pesquisa foi feita para
mostrar **quanto o faturamento sobe ou cai**. Por isso o dado vem como
**número-índice**.

**Base 2022 = 100** — a média mensal de 2022 vale 100. Assim:

- índice **118,5** = o mês faturou 18,5% a mais que a média de 2022;
- índice **95** = faturou 5% a menos.

Dá para comparar quaisquer dois meses dividindo um índice pelo outro. Varejo de
SP: abril/2025 = 118,5 e abril/2024 = 104,2 → 118,5 ÷ 104,2 = **+13,8%**.

## 3. Nominal × real (descontar a inflação)

- **Nominal** — em reais do momento, do jeito que entra no caixa. Inclui o
  aumento de preços.
- **Real** — com a inflação descontada. Mostra se o setor cresceu de verdade.

Crescer 5% num ano em que a inflação foi 5% é ficar parado. Por isso o dataset
traz o IPCA junto, e a conta é:

```
indice_real = indice_receita / ipca
```

Exemplo — varejo de SP, abril/2025 contra abril/2024:

| | Variação |
|---|---|
| Faturamento (nominal) | +13,8% |
| Inflação (IPCA) | +5,5% |
| **Crescimento real** | **+7,8%** (1,138 ÷ 1,055 − 1) |

## 4. Sazonalidade

**Sazonalidade** é um padrão que se repete todo ano no mesmo mês. No varejo de
SP, o índice de dezembro/2024 foi **142** e o de fevereiro/2024, **101**:
dezembro vende cerca de 40% mais por causa do Natal, todo ano.

Por isso **não se compara dezembro com novembro** para dizer se o setor está
melhorando. A comparação certa é com o **mesmo mês do ano anterior**
(dezembro/2025 × dezembro/2024) — o efeito do calendário se cancela.

## 5. O que o IBGE oferece e o que usamos

Cada tabela traz várias versões do dado. Usamos só uma:

| Versão | Usamos? | Por quê |
|---|---|---|
| Índice de **receita nominal**, sem ajuste sazonal | **sim** | é o faturamento, do jeito que aconteceu |
| Índice de volume | não | desconta os preços do próprio setor e mede quantidade vendida, não faturamento |
| Índice com ajuste sazonal | não | apaga o efeito do Natal e de outras datas, que é faturamento real |
| Variações % prontas | não | são calculadas a partir do próprio índice; fazemos essa conta quando precisar |

## 6. O arquivo

Uma linha por **setor × estado × mês** (o chamado formato longo):

```
setor;uf;ano;mes;indice_receita;ipca;dolar;selic
COMERCIO_VAREJISTA;SP;2025;4;118,53521;7276,54;5,7837;14,15
```

- `uf = BR` é o Brasil inteiro.
- IPCA, dólar e Selic são nacionais: o valor do mês se repete em todos os
  estados.
- Separador `;` e decimal `,` para abrir direto no Excel em português.

Cada combinação setor × estado ao longo do tempo é uma **série temporal**: são
54 séries de estados (27 × 2) mais as 2 do Brasil.

## 7. Perguntas que podem aparecer na apresentação

**Por que não mostrar o faturamento em reais?**
O IBGE não publica esse valor mensal. A pesquisa acompanha uma amostra de
empresas e divulga a variação do faturamento, que é o que interessa para prever
crescimento.

**Por que só varejo e serviços?**
São os setores em que o IBGE publica faturamento mensal por estado. A indústria
tem pesquisa mensal só de quantidade produzida, e o agro não tem dado mensal de
faturamento por estado.

**O que significa o 100?**
É a média mensal de 2022. Serve só de referência para comparar os meses.

**Por que descontar a inflação?**
Sem isso, todo setor parece crescer, porque os preços sobem. O crescimento real
mostra quem vendeu mais de verdade.

**Os dados representam todas as empresas?**
Não. Representam empresas formais com 20 ou mais pessoas ocupadas; pequenos
negócios e informais ficam de fora.

**Por que trazer dólar e Selic?**
Porque afetam o consumo: juros altos encarecem o crédito e o parcelamento, e o
dólar mexe nos preços. Eles entram como informação extra para o modelo prever o
faturamento.

**Os dados são confiáveis?**
São estatísticas oficiais do IBGE e do Banco Central, usadas pelo governo e pelo
mercado para acompanhar a economia.
