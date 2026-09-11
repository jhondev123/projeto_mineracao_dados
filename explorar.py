"""Mostra as variaveis e classificacoes de uma tabela do SIDRA.

Util para conferir se a tabela tem o que voce precisa antes de coletar.

Uso:
    python explorar.py 8688
"""

import sys

import sidra


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: python explorar.py <numero_da_tabela>")

    tabela = sys.argv[1]
    meta = sidra.metadados(tabela)

    print(f"Tabela {tabela}: {meta.get('nome')}")
    print(f"Periodicidade: {meta.get('periodicidade')}")
    print(f"Niveis territoriais: {meta.get('nivelTerritorial')}")

    print("\nVariaveis:")
    for variavel in meta.get("variaveis", []):
        print(f"  {variavel['id']:>6}  {variavel['nome']}  ({variavel['unidade']})")

    print("\nClassificacoes:")
    for classificacao in meta.get("classificacoes", []):
        print(f"  {classificacao['id']} - {classificacao['nome']}")
        for categoria in classificacao.get("categorias", []):
            print(f"      {categoria['id']:>8}  {categoria['nome']}")


if __name__ == "__main__":
    main()
