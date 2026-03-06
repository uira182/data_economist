"""
Script executável para testar bcb_sgs.get(codigo).

Uso (na raiz do projeto ou com PYTHONPATH):
    python tests/run_bcb_sgs_tests.py

Ou, com o pacote instalado:
    pip install -e .
    python tests/run_bcb_sgs_tests.py
"""
from __future__ import annotations

import sys

# Garantir que o pacote está no path quando executado a partir de tests/
if __name__ == "__main__":
    import os
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if os.path.isdir(raiz):
        src = os.path.join(raiz, "src")
        if os.path.isdir(src) and src not in sys.path:
            sys.path.insert(0, src)


def main() -> int:
    from data_economist import bcb_sgs

    print("=== Testes BCB SGS (executável) ===\n")

    # 1. Import
    print("1. Import: from data_economist import bcb_sgs ... OK")
    assert hasattr(bcb_sgs, "get"), "bcb_sgs.get não encontrado"

    # 2. get(433) — IPCA
    print("2. bcb_sgs.get(433) ...")
    dados = bcb_sgs.get(433)
    assert isinstance(dados, list), "Resultado deve ser lista"
    assert len(dados) > 0, "Série 433 (IPCA) deve ter dados"
    print(f"   OK — {len(dados)} pontos (primeiro: {dados[0]}, último: {dados[-1]})")

    # 3. Estrutura
    for item in dados[:3]:
        assert "data" in item and "valor" in item, "Cada item deve ter 'data' e 'valor'"
    print("3. Estrutura: cada item tem 'data' e 'valor' ... OK")

    # 4. Ordem cronológica
    datas = [item["data"] for item in dados]
    ordenado = sorted(datas, key=lambda d: (d[-4:], d[3:5], d[:2]))
    assert datas == ordenado, "Dados devem estar em ordem cronológica"
    print("4. Ordem cronológica ... OK")

    # 5. Código como str
    d2 = bcb_sgs.get("433")
    assert len(d2) == len(dados), "get('433') deve dar mesmo tamanho que get(433)"
    print("5. bcb_sgs.get('433') aceito ... OK")

    print("\n=== Todos os testes passaram. ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nERRO: {e}")
        sys.exit(1)
