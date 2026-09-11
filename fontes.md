# Fontes dos dados

Todas as fontes são públicas e oficiais, acessadas por API sem autenticação.
Data de acesso: 11/09/2026.

## 1. IBGE — API de Agregados (SIDRA)

- API: `https://servicodados.ibge.gov.br/api/v3/agregados`
- Documentação: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3
- Consulta das tabelas no navegador: `https://sidra.ibge.gov.br/tabela/<número>`

### Índices mensais (dão o movimento mês a mês)

Em todas foi usado só o **Número-índice (2022=100) sem ajuste sazonal**, tipo
**receita nominal** (na PIM-PF, produção física).

| Tabela | Pesquisa | Conteúdo | Usada em |
|---|---|---|---|
| [8880](https://sidra.ibge.gov.br/tabela/8880) | PMC — Pesquisa Mensal de Comércio | Receita nominal do comércio varejista | COMERCIO_VAREJISTA; `coleta.py` |
| [8881](https://sidra.ibge.gov.br/tabela/8881) | PMC | Receita nominal do varejo ampliado | `coleta.py` |
| [8884](https://sidra.ibge.gov.br/tabela/8884) | PMC | Receita nominal de veículos, motocicletas, partes e peças | COMERCIO_VEICULOS |
| [5906](https://sidra.ibge.gov.br/tabela/5906) | PMS — Pesquisa Mensal de Serviços | Receita nominal de serviços (total por UF) | SERVICOS |
| [8693](https://sidra.ibge.gov.br/tabela/8693) | PMS | Receita nominal por atividade de serviços, por UF | SERVICOS_* |
| [8688](https://sidra.ibge.gov.br/tabela/8688) | PMS | Receita nominal por atividade e subdivisões (Brasil) | `coleta.py` |
| [8888](https://sidra.ibge.gov.br/tabela/8888) | PIM-PF — Pesquisa Industrial Mensal – Produção Física | Produção física por seção industrial, por UF | INDUSTRIA* |
| [6903](https://sidra.ibge.gov.br/tabela/6903) | IPP — Índice de Preços ao Produtor | Preço ao produtor por seção industrial (Brasil, dez/2018=100) | INDUSTRIA* |

### Valores anuais em R$ por UF (dão o nível, ano de referência 2024)

| Tabela | Pesquisa | Variável | Usada em |
|---|---|---|---|
| [10653](https://sidra.ibge.gov.br/tabela/10653) | PAC — Pesquisa Anual de Comércio | Receita bruta de revenda de mercadorias (mil R$), por grupo de comércio | COMERCIO_* |
| [10762](https://sidra.ibge.gov.br/tabela/10762) | PAS — Pesquisa Anual de Serviços | Receita bruta de serviços (mil R$), por atividade | SERVICOS* |
| [10457](https://sidra.ibge.gov.br/tabela/10457) | PIA-Empresa — Pesquisa Industrial Anual | Total de receitas líquidas de vendas (mil R$), por seção CNAE | INDUSTRIA* |

## 2. Comex Stat — Ministério do Desenvolvimento, Indústria, Comércio e Serviços (MDIC)

- API: `POST https://api-comexstat.mdic.gov.br/general`
- Documentação: https://api-comexstat.mdic.gov.br/docs
- Portal: https://comexstat.mdic.gov.br
- Consulta usada: exportação (`flow: export`), mensal, filtro **ISIC Seção A –
  Agropecuária**, detalhada por **UF do produto** (estado onde a mercadoria foi
  produzida, não a sede do exportador), métrica **US$ FOB**.
- Usada em: AGRO_EXPORTACAO.
- A API não devolve linha para mês sem exportação; esses meses entram com valor
  0 (acontece em UFs pequenas: AP, SE, RR, DF, TO, AC, PI).
- Por ser ISIC Seção A, entram só produtos primários (soja em grão, milho, café
  não torrado, algodão bruto, frutas, animais vivos...). Carne, açúcar, farelo e
  suco são Indústria de Transformação e ficam de fora, para não duplicar com o
  segmento INDUSTRIA.

## 3. Banco Central do Brasil — SGS (Sistema Gerenciador de Séries Temporais)

- Série **3698** — Taxa de câmbio livre, dólar americano (venda), média mensal (R$/US$)
- API: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.3698/dados?formato=json`
- Portal: https://www3.bcb.gov.br/sgspub
- Usada para converter a exportação agro de US$ para R$ (valor FOB do mês × câmbio médio do mês).

## Fontes de agro consultadas e não usadas

Nenhuma fonte oficial publica **receita mensal do agro em R$ por UF**. As que
existem:

| Fonte | O que tem | Por que ficou de fora |
|---|---|---|
| IBGE PAM, tabela [5457](https://sidra.ibge.gov.br/tabela/5457) | Valor da produção das lavouras (mil R$) por UF | Anual — não dá série mensal |
| IBGE PPM, tabela [74](https://sidra.ibge.gov.br/tabela/74) | Valor da produção de origem animal (leite, ovos, mel...) por UF | Anual e não inclui carne |
| IBGE LSPA, tabela [6588](https://sidra.ibge.gov.br/tabela/6588) | Estimativa mensal da safra do ano (toneladas) por UF | É previsão da safra anual, em quantidade |
| IBGE Abate trimestral, tabelas [1092](https://sidra.ibge.gov.br/tabela/1092)/[1093](https://sidra.ibge.gov.br/tabela/1093)/[1094](https://sidra.ibge.gov.br/tabela/1094) | Cabeças e peso de carcaças abatidas, por mês e UF | Quantidade, sem valor |
| IBGE Leite trimestral, tabela [1086](https://sidra.ibge.gov.br/tabela/1086) | Leite adquirido pela indústria, por mês e UF | Só um produto |
| MAPA — [Valor Bruto da Produção Agropecuária (VBP)](https://www.gov.br/agricultura/pt-br/assuntos/politica-agricola/valor-bruto-da-producao-agropecuaria-vbp) | Valor da produção por produto e UF (planilha "VBP Regional") | Valor anual (atualizado todo mês), não série mensal; planilha, sem API |

Se o trabalho precisar do tamanho do agro por estado (e não da variação mensal),
PAM + PPM ou o VBP do MAPA são as referências; dá para citar como contexto na
apresentação.

## Como citar (ABNT)

- IBGE. Sistema IBGE de Recuperação Automática – SIDRA. Rio de Janeiro: IBGE, 2026. Disponível em: https://sidra.ibge.gov.br. Acesso em: 11 set. 2026.
- BRASIL. Ministério do Desenvolvimento, Indústria, Comércio e Serviços. Comex Stat. Brasília, 2026. Disponível em: https://comexstat.mdic.gov.br. Acesso em: 11 set. 2026.
- BANCO CENTRAL DO BRASIL. Sistema Gerenciador de Séries Temporais – SGS, série 3698. Brasília, 2026. Disponível em: https://www3.bcb.gov.br/sgspub. Acesso em: 11 set. 2026.
