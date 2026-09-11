# Guia de termos técnicos

Glossário dos conceitos que foi preciso entender para montar o dataset
(`dados/faturamento_uf_mensal_*.csv`). Segue a ordem do caminho percorrido: de
onde vêm os dados → o que os números significam → como foram combinados.

Fontes e links: [fontes.md](fontes.md). Etapas do projeto: [crisp.md](crisp.md).

---

## 1. Como o IBGE organiza os dados

**IBGE** — Instituto Brasileiro de Geografia e Estatística, órgão oficial de
estatísticas do Brasil.

**SIDRA** — Sistema IBGE de Recuperação Automática, o banco de tabelas do IBGE
(sidra.ibge.gov.br). A **API de Agregados** é o acesso a esse banco por
programa: você pede por URL e recebe JSON.

**Tabela (ou agregado)** — conjunto de dados publicado com um número fixo (ex.:
8880). Quando a pesquisa muda de metodologia ou de ano-base, o IBGE encerra a
tabela e cria outra (ex.: a 8185, base 2014=100, foi encerrada em dez/2022 e
substituída pela 8880, base 2022=100).

**Variável** — o que a tabela mede (ex.: "Número-índice", "Variação M/M-12",
"Receita bruta de serviços"). Cada uma tem um id e uma unidade (%,
número-índice, mil reais).

**Classificação e categoria** — as quebras da tabela. A classificação é o eixo
(ex.: *Atividades de serviços*) e as categorias são os valores dele (ex.:
*Transportes*, *Serviços prestados às famílias*). Na API, `12355[106876]` quer
dizer classificação 12355, categoria 106876.

**Nível territorial** — o recorte geográfico: `N1` Brasil, `N2` Grande Região,
`N3` Unidade da Federação (estado). Nem toda tabela tem todos os níveis — por
isso algumas séries só existem para 12 ou 17 UFs.

**Período** — `AAAAMM` nas tabelas mensais (202504 = abril de 2025) e `AAAA` nas
anuais.

**Metadados** — a ficha da tabela: variáveis, classificações, níveis e períodos
disponíveis. É o que o `explorar.py` mostra.

**Símbolos especiais** — no lugar de um número, a API pode devolver:

| Símbolo | Significado |
|---|---|
| `-` | zero absoluto (não houve) |
| `0` | zero por arredondamento (existe, mas é muito pequeno) |
| `X` | valor omitido por **sigilo estatístico**: há poucas empresas no recorte e publicar identificaria alguma delas |
| `..` | não se aplica |
| `...` | dado não disponível |

## 2. As pesquisas

Pesquisas **conjunturais** são mensais e mostram o movimento de curto prazo,
quase sempre como índice. Pesquisas **estruturais** são anuais, mais detalhadas
e trazem valores em reais, mas saem com 1 a 2 anos de atraso. O dataset junta
as duas.

| Sigla | Nome | Frequência | O que mede |
|---|---|---|---|
| PMC | Pesquisa Mensal de Comércio | mensal | receita e volume de vendas do varejo (índice) |
| PMS | Pesquisa Mensal de Serviços | mensal | receita e volume dos serviços (índice) |
| PIM-PF | Pesquisa Industrial Mensal – Produção Física | mensal | quantidade produzida pela indústria (índice) |
| IPP | Índice de Preços ao Produtor | mensal | preço de venda da indústria "na porta da fábrica", sem impostos e frete |
| IPCA | Índice Nacional de Preços ao Consumidor Amplo | mensal | inflação oficial do país (usado na preparação, fase 3) |
| PAC | Pesquisa Anual de Comércio | anual | receita, pessoal e salários das empresas comerciais (R$) |
| PAS | Pesquisa Anual de Serviços | anual | o mesmo, para empresas de serviços (R$) |
| PIA-Empresa | Pesquisa Industrial Anual | anual | o mesmo, para a indústria (R$) |
| PAM / PPM | Produção Agrícola / Pecuária Municipal | anual | produção e valor da produção do agro (consultadas, não usadas) |
| LSPA | Levantamento Sistemático da Produção Agrícola | mensal | previsão da safra do ano, em toneladas (consultada, não usada) |

## 3. Índices e variações

**Número-índice** — número sem unidade que compara um valor com um período de
referência, a **base**. Não é R$.

**Base 2022 = 100** — a média dos 12 meses de 2022 vale 100. Um índice de 118,5
em abril/2025 quer dizer que a receita daquele mês foi 18,5% maior que a média
mensal de 2022. Dá para comparar meses entre si (118,5 ÷ 104,2 = +13,8%), mas o
índice não diz quantos reais foram.

**Receita nominal** — valor em reais correntes, do jeito que entra no caixa,
com o efeito da inflação. **É o que corresponde a faturamento.**

**Volume** — a receita nominal **deflacionada**: descontado o aumento de preços,
mostra se foi vendida mais *quantidade*. Exemplo: receita +10% com preços +6% →
volume ≈ +3,8% (1,10 ÷ 1,06 − 1).

**Deflacionar / deflator** — dividir um valor nominal por um índice de preços (o
deflator) para tirar a inflação. O resultado é o valor **real**, a preços de uma
data fixa.

**Sazonalidade** — padrão que se repete todo ano no mesmo mês. No varejo de SP o
índice de dez/2024 foi 142 e o de fev/2024, 101: dezembro vende ~40% mais por
causa do Natal, todo ano.

**Ajuste sazonal** — tratamento estatístico que remove a sazonalidade para
comparar meses vizinhos (dezembro com novembro) sem a distorção do Natal. Não
usamos: o objetivo é o faturamento de verdade, e dezembro faturar mais **é**
real.

**Variações que a API também entrega** (todas calculáveis a partir do
número-índice):

| Nome | Compara | Exemplo em abr/2025 |
|---|---|---|
| M/M-1 | o mês com o anterior, com ajuste sazonal | abr/25 × mar/25 |
| M/M-12 | o mês com o mesmo mês do ano anterior | abr/25 × abr/24 |
| Acumulada no ano | janeiro até o mês × mesmo período do ano anterior | jan–abr/25 × jan–abr/24 |
| Acumulada em 12 meses | últimos 12 meses × os 12 anteriores | mai/24–abr/25 × mai/23–abr/24 |

**Por que só uma variável foi usada:** das várias que a API devolve, ficamos com
o **número-índice sem ajuste sazonal, tipo receita nominal**. Volume não é
faturamento, o ajuste sazonal apaga um efeito real, e as variações % são
derivadas do índice (dá para recalcular quando precisar).

## 4. Conceitos contábeis

**Faturamento** — termo do dia a dia para o total vendido. Nas pesquisas aparece
como *receita*.

**Receita bruta** — total das vendas antes de descontar impostos sobre vendas,
devoluções e descontos.

**Receita líquida** — receita bruta menos essas deduções.

**Receita bruta de revenda de mercadorias** (PAC) — o que o comércio fatura
revendendo produtos que comprou.

**Receita bruta de serviços** (PAS) — o que as empresas faturam prestando
serviços.

**Receitas líquidas de vendas** (PIA) — o que a indústria fatura vendendo o que
produziu, já sem impostos. Casa com o IPP, que também é preço sem impostos.

**Valor Bruto da Produção (VBP)** — quantidade produzida × preço médio. No agro,
o MAPA chama de "faturamento dentro da porteira". Mede o que foi produzido, não
necessariamente o que foi vendido.

**Mil reais** — unidade das tabelas anuais: `1021602669` mil reais =
R$ 1.021.602.669.000 (R$ 1,02 trilhão). O `dataset.py` multiplica por 1.000.

**Unidade local** — cada endereço físico da empresa (loja, fábrica). A PIA por UF
conta a receita onde fica a fábrica, não onde está a sede.

## 5. Classificação de atividades

**CNAE 2.0** — Classificação Nacional de Atividades Econômicas. Organiza toda
atividade econômica em níveis: **seção** (letra), **divisão** (2 dígitos),
**grupo** (3), **classe** (4). Seções que aparecem no projeto:

| Seção | Atividade |
|---|---|
| A | agricultura, pecuária, produção florestal, pesca |
| B | indústrias extrativas (petróleo, minério) |
| C | indústrias de transformação (alimentos, veículos, química...) |
| G | comércio e reparação de veículos |
| H, I, J, L, M, N, R, S | serviços (transporte, alojamento e alimentação, informação, imobiliárias, profissionais, administrativos...) |

**ISIC** — International Standard Industrial Classification, a classificação da
ONU. A CNAE é derivada dela e as seções têm as mesmas letras. O Comex Stat usa a
ISIC, por isso "ISIC Seção A" = agropecuária.

**Indústria geral = extrativa + transformação.**
- **Extrativa**: retira recursos da natureza (petróleo, minério de ferro).
- **Transformação**: transforma matéria-prima em produto (soja → farelo, minério
  → aço).

**Varejo restrito × ampliado** (PMC):
- **Varejo (restrito)**: supermercados, combustíveis, vestuário, móveis e
  eletrodomésticos, farmácias, livrarias, informática e outros.
- **Varejo ampliado**: o restrito + veículos, motos e peças + material de
  construção + atacado de alimentos (desde 2022).

**Atacado** — venda para outras empresas (para revenda ou uso), não para o
consumidor final.

## 6. Comércio exterior e câmbio

**Comex Stat** — sistema do MDIC (Ministério do Desenvolvimento, Indústria,
Comércio e Serviços) com as estatísticas oficiais de exportação e importação,
tiradas das declarações registradas no Siscomex.

**FOB (Free On Board)** — valor da mercadoria já colocada no navio no porto de
saída, **sem** frete e seguro internacionais. É o padrão para medir exportação.
Na importação aparece também o **CIF**, que inclui frete e seguro.

**UF do produto** — o estado onde a mercadoria foi produzida, não o da empresa
exportadora nem o do porto. Soja plantada no MT e embarcada em Santos conta
para MT.

**NCM / SH** — códigos de produto do comércio exterior (a NCM, de 8 dígitos, é a
versão Mercosul do Sistema Harmonizado internacional). Não usamos direto:
filtramos pela ISIC.

**Taxa de câmbio média mensal** — média do dólar (R$ por US$) no mês, calculada
pelo Banco Central; série 3698 do **SGS** (Sistema Gerenciador de Séries
Temporais do BCB). Cada mês é convertido com o câmbio daquele mês:
`valor_R$ = valor_US$_FOB × câmbio_médio`.

## 7. Técnicas usadas para montar o dataset

### Ancoragem (benchmarking)

Combinar uma série **mensal em índice** com um valor **anual em reais** para
obter um valor mensal em reais. A família de métodos se chama **desagregação
temporal** (Denton e Chow-Lin são os mais conhecidos); usamos a versão mais
simples, proporcional:

```
valor_mes = receita_anual_2024 × indice_mes / soma dos 12 índices de 2024
```

Exemplo real — varejo de São Paulo, abril de 2025:

| Dado | Fonte | Valor |
|---|---|---|
| Receita bruta de revenda do varejo SP em 2024 | PAC, tabela 10653 | 1.021.602.669 mil R$ |
| Soma dos 12 índices de 2024 | PMC, tabela 8880 | 1.359,647 |
| Índice de abril/2025 | PMC, tabela 8880 | 118,535 |

`1.021.602.669.000 × 118,535 ÷ 1.359,647 = R$ 89.064.213.991` — o mesmo valor
que está no CSV.

Dividir pela **soma** dos índices de 2024 garante que os 12 meses de 2024 somem
exatamente a receita anual oficial.

**Consequência importante:** o fator (receita anual ÷ soma dos índices) é
constante em cada série, então **as variações % do dataset são idênticas às do
índice oficial**. Conferido: abr/2025 contra abr/2024 dá +13,80% no CSV e +13,8%
na variação M/M-12 publicada pelo IBGE. A estimativa mexe só no **nível** em
reais (e, portanto, na comparação de tamanho entre setores); o **movimento** é
o dado oficial.

Exceções: INDUSTRIA\* (o movimento vem do proxy abaixo) e AGRO_EXPORTACAO (não é
ancorado, já é valor em R$).

### Proxy

Variável substituta, usada quando a desejada não existe. Na indústria não há
índice mensal de receita, então:

```
receita ≈ quantidade × preço   →   índice de receita ≈ PIM-PF (quantidade) × IPP (preço)
```

Limitação: o IPP é nacional, então o mesmo preço vale para todos os estados.

### Dupla contagem e a coluna `nivel`

Dupla contagem é somar a mesma receita duas vezes: SERVICOS já contém
SERVICOS_TRANSPORTES, e somar os dois conta os transportes duas vezes. A coluna
`nivel` separa:
- `setor` — segmentos que não se sobrepõem (podem ser somados);
- `subsetor` — abertura de SERVICOS e INDUSTRIA (não somar com `setor`).

Pelo mesmo motivo o agro entra só com produtos primários (ISIC A): carne e
açúcar são indústria de transformação e já estão em INDUSTRIA.

### Estimativa × dado oficial

- **Dado oficial**: publicado pelo órgão (índices, receitas anuais, exportação).
- **Estimativa**: calculada a partir de dados oficiais com um método nosso (o
  valor mensal em R$). Na apresentação, falar em faturamento mensal
  **estimado**.

## 8. Formato dos dados

**Série temporal** — valores de uma mesma coisa ao longo do tempo. No dataset,
cada combinação `segmento × UF` é uma série (ex.: SERVICOS em SP, de jan/2012 a
jul/2026). São 198 séries.

**Formato longo (tidy) × largo (wide)**

Longo (o do dataset) — uma linha por observação:
```
segmento;uf;ano;mes;valor
SERVICOS;SP;2025;4;142433645451
SERVICOS;RJ;2025;4;...
```
Largo — uma coluna por série:
```
ano;mes;SERVICOS_SP;SERVICOS_RJ;...
2025;4;142433645451;...
```
O longo é melhor para filtrar e agrupar; o largo é o que muitos gráficos e
modelos pedem. Em pandas:
`df.pivot_table(index=["ano", "mes"], columns=["segmento", "uf"], values="valor")`.

**CSV com `;` e BOM UTF-8** — o Excel em português usa vírgula como decimal, por
isso as colunas são separadas por `;`. O BOM é um marcador invisível no início
do arquivo que faz o Excel reconhecer os acentos.

**Zero × ausente** — zero é "não houve" (mês sem exportação agro no AP); ausente
é "não se sabe" (UF que a pesquisa não cobre). No dataset, ausente = a linha não
existe.

**Outlier** — valor muito fora do padrão. Os maiores do dataset têm causa
conhecida: pandemia (abr–mai/2020) e enchente do RS (mai/2024). Não são erro;
como tratá-los é decisão da preparação ([crisp.md](crisp.md), fase 3).

**Cobertura** — quantas UFs e meses cada série tem. Varia porque as pesquisas
mensais só abrem atividade nos estados com amostra suficiente (12 UFs na PMS por
atividade, 17 na PIM-PF).
