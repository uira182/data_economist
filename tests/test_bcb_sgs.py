"""Testes do módulo BCB SGS (Banco Central — Sistema Gerenciador de Séries)."""

import pytest
import requests

from data_economist import bcb_sgs


# Série real: IPCA (código 433)
CODIGO_IPCA = 433


def test_import_bcb_sgs():
    """from data_economist import bcb_sgs expõe o módulo com .get()."""
    assert hasattr(bcb_sgs, "get")


def test_get_retorna_lista():
    """bcb_sgs.get(codigo) devolve uma lista."""
    dados = bcb_sgs.get(CODIGO_IPCA)
    assert isinstance(dados, list)


def test_get_retorna_dicts_com_data_valor():
    """Cada elemento da lista tem chaves 'data' e 'valor'."""
    dados = bcb_sgs.get(CODIGO_IPCA)
    assert len(dados) > 0
    for item in dados:
        assert isinstance(item, dict)
        assert "data" in item
        assert "valor" in item


def test_get_ordem_cronologica():
    """Os dados vêm em ordem cronológica (mais antigo primeiro)."""
    dados = bcb_sgs.get(CODIGO_IPCA)
    assert len(dados) >= 2
    # Formato DD/MM/YYYY — comparação como string funciona para esse formato
    datas = [item["data"] for item in dados]
    assert datas == sorted(datas, key=lambda d: (d[-4:], d[3:5], d[:2]))


def test_get_aceita_int_ou_str():
    """bcb_sgs.get() aceita código como int ou str."""
    d1 = bcb_sgs.get(433)
    d2 = bcb_sgs.get("433")
    assert isinstance(d1, list) and isinstance(d2, list)
    assert len(d1) == len(d2)
    assert d1[0] == d2[0]


def test_get_ultimo_valor_coerente():
    """O último valor da série é recente (ano >= 2020)."""
    dados = bcb_sgs.get(CODIGO_IPCA)
    assert len(dados) > 0
    ultima_data = dados[-1]["data"]
    ano = int(ultima_data[-4:])
    assert ano >= 2020


def test_get_codigo_invalido_levanta():
    """Código de série inexistente deve levantar exceção (timeout curto para não travar)."""
    with pytest.raises((requests.HTTPError, ValueError, requests.exceptions.Timeout)):
        bcb_sgs.get(999999999, timeout=5)


def test_get_com_date_init():
    """bcb_sgs.get(codigo, date_init) retorna dados a partir da data inicial até o último valor."""
    dados = bcb_sgs.get(CODIGO_IPCA, date_init="2020-01-01")
    assert isinstance(dados, list) and len(dados) > 0
    primeira_data = dados[0]["data"]
    ano_primeiro = int(primeira_data[-4:])
    assert ano_primeiro >= 2020, "Com date_init=2020-01-01 o primeiro ano deve ser >= 2020"


def test_get_com_date_init_e_date_end():
    """bcb_sgs.get(codigo, date_init, date_end) retorna só o intervalo pedido."""
    dados = bcb_sgs.get(CODIGO_IPCA, date_init="2020-01-01", date_end="2025-01-01")
    assert isinstance(dados, list) and len(dados) > 0
    anos = [int(d["data"][-4:]) for d in dados]
    assert min(anos) >= 2020 and max(anos) <= 2025


def test_get_só_date_end():
    """bcb_sgs.get(codigo, None, date_end) usa date_end como data final e volta 10 em 10 anos."""
    dados = bcb_sgs.get(CODIGO_IPCA, None, "2000-01-06")
    assert isinstance(dados, list) and len(dados) > 0
    # Último ponto deve ser próximo de 2000-01-06 (data final pedida)
    ultima_data = dados[-1]["data"]
    # Formato DD/MM/YYYY
    from datetime import datetime
    dt = datetime.strptime(ultima_data, "%d/%m/%Y")
    assert dt.year <= 2000, "Com date_end=2000-01-06 o último ponto deve ser até 2000"
