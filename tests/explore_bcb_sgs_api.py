"""
Script de exploração da API BCB SGS (Sistema Gerenciador de Séries Temporais).

Objetivo: analisar respostas da API para implementar bcb_sgs.get(codigo).
- Endpoint base: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
- Parâmetros obrigatórios: dataInicial, dataFinal (DD/MM/YYYY), intervalo máx. 10 anos.
- Endpoint últimos N valores: .../dados/ultimos/{N}?formato=json

Execute: python tests/explore_bcb_sgs_api.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta

import requests

BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
CODIGO_EXEMPLO = 433  # IPCA
CODIGO_INVALIDO = 999999999


def _fmt(d: datetime) -> str:
    return d.strftime("%d/%m/%Y")


def test_ultimos_n():
    """Testa o endpoint /dados/ultimos/{N} para obter o último valor (e assim a data final)."""
    url = f"{BASE}.{CODIGO_EXEMPLO}/dados/ultimos/1?formato=json"
    print("1. Endpoint últimos 1 valor:", url)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    print("   Resposta:", json.dumps(data, indent=2, ensure_ascii=False))
    if isinstance(data, list) and len(data) > 0:
        ultima_data = data[-1].get("data")
        print("   Última data da série:", ultima_data)
        return ultima_data
    return None


def test_janela_10_anos():
    """Testa uma janela de 10 anos (dataInicial e dataFinal)."""
    data_final = "05/03/2026"
    # 10 anos antes
    dt = datetime.strptime(data_final, "%d/%m/%Y")
    dt_inicial = dt - timedelta(days=10 * 365)
    data_inicial = _fmt(dt_inicial)
    url = f"{BASE}.{CODIGO_EXEMPLO}/dados?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    print("2. Janela ~10 anos:", url)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        print("   Quantidade de pontos:", len(data))
        if data:
            print("   Primeiro:", data[0])
            print("   Último:", data[-1])
    else:
        print("   Resposta (não é lista):", data)


def test_serie_inexistente():
    """Série inexistente: API pode retornar 200 com mensagem, 404 ou timeout."""
    url = f"{BASE}.{CODIGO_INVALIDO}/dados/ultimos/1?formato=json"
    print("3. Série inexistente (ultimos/1):", url)
    try:
        r = requests.get(url, timeout=10)
        print("   Status:", r.status_code)
        print("   Texto:", r.text[:200] if r.text else "(vazio)")
        try:
            j = r.json()
            print("   JSON:", j)
        except Exception as e:
            print("   JSON inválido:", e)
    except requests.exceptions.Timeout:
        print("   (timeout - API pode demorar ou travar em código inválido)")


def test_janela_vazia():
    """Janela com dataInicial > dataFinal ou fora do histórico."""
    url = f"{BASE}.{CODIGO_EXEMPLO}/dados?formato=json&dataInicial=01/01/1900&dataFinal=01/01/1901"
    print("4. Janela antiga (pode vir vazia):", url)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    print("   É lista:", isinstance(data, list))
    if isinstance(data, list):
        print("   Quantidade:", len(data))
        if data:
            print("   Primeiro:", data[0])


def main():
    print("=== Exploração API BCB SGS ===\n")
    test_ultimos_n()
    print()
    test_janela_10_anos()
    print()
    test_serie_inexistente()
    print()
    test_janela_vazia()
    print("\n=== Fim ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
