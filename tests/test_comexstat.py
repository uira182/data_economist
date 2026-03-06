"""Testes do módulo ComexStat (MDIC — comércio exterior)."""

import pytest
import requests

from data_economist import comexstat


# Body no padrão da documentação oficial (exemplo do usuário)
BODY_EXEMPLO = {
    "flow": "export",
    "monthDetail": False,
    "period": {"from": "2018-01", "to": "2018-01"},
    "filters": [{"filter": "state", "values": [26]}],
    "details": ["country", "state"],
    "metrics": ["metricFOB", "metricKG"],
}


def test_import_comexstat():
    """from data_economist import comexstat expõe .get(), .get_general(), .get_filter(), .get_by_filter()."""
    assert hasattr(comexstat, "get")
    assert hasattr(comexstat, "get_general")
    assert hasattr(comexstat, "get_filter")
    assert hasattr(comexstat, "get_by_filter")


def test_get_aceita_body_dict():
    """comexstat.get(body) aceita um dicionário no padrão da documentação."""
    resultado = comexstat.get(BODY_EXEMPLO, timeout=60)
    assert isinstance(resultado, (dict, list)), "Resposta deve ser dict ou list"


def test_get_resposta_tem_estrutura_esperada():
    """Se a API retornar sucesso, a resposta tem 'data' ou é lista."""
    resultado = comexstat.get(BODY_EXEMPLO, timeout=60)
    if isinstance(resultado, dict):
        # Resposta típica: {"data": [...], "success": true, ...}
        assert "data" in resultado or "success" in resultado or len(resultado) > 0
    else:
        assert isinstance(resultado, list)


def test_get_body_invalido_levanta():
    """Body com filtro inexistente ou formato inválido pode retornar 400."""
    body_ruim = {
        "flow": "export",
        "monthDetail": False,
        "period": {"from": "2018-01", "to": "2018-01"},
        "filters": [{"filter": "filtro_inexistente_xyz", "values": [1]}],
        "details": [],
        "metrics": ["metricFOB"],
    }
    with pytest.raises(requests.HTTPError):
        comexstat.get(body_ruim, timeout=30)


# ---- Testes com get_general (mapeamentos do notebook — retornam dados) ----


def _extrair_lista(resultado):
    """GET /general pode devolver resultado['list'] ou resultado['data']['list']; POST resultado['data']."""
    if isinstance(resultado, list):
        return resultado
    if not isinstance(resultado, dict):
        return resultado
    # Chave direta "list" (GET /general)
    lst = resultado.get("list")
    if isinstance(lst, list):
        return lst
    # Chave "data" (POST ou GET aninhado)
    data = resultado.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        lst = data.get("list")
        if isinstance(lst, list):
            return lst
    return resultado


def test_get_general_export_cuci_group_retorna_dados():
    """GET /general — export, cuciGroup 281b, metricFOB (notebook: BALANÇA). Retorna dados."""
    resultado = comexstat.get_general("export", "cuciGroup", ["281b"], "metricFOB", timeout=60)
    assert isinstance(resultado, (dict, list))
    data = _extrair_lista(resultado)
    assert isinstance(data, list), "Resposta deve conter lista de registos (chave 'list' ou 'data')"
    assert len(data) > 0, "Consulta export cuciGroup 281b deve retornar pelo menos um registro"


def test_get_general_import_chapter4_retorna_dados():
    """GET /general — import, chapter4 2603 (minério de cobre), metricKG (notebook). Retorna dados."""
    resultado = comexstat.get_general("import", "chapter4", ["2603"], "metricKG", timeout=60)
    assert isinstance(resultado, (dict, list))
    data = _extrair_lista(resultado)
    assert isinstance(data, list), "Resposta deve conter lista de registos (chave 'list' ou 'data')"
    assert len(data) > 0, "Consulta import chapter4 2603 deve retornar pelo menos um registro"


# ---- Filtro guardado (ID ou URL) ----


def test_get_filter_retorna_data_id_filter_createdAt():
    """GET /filter/{id} retorna data.id, data.filter (string JSON), data.createdAt."""
    resp = comexstat.get_filter(146862, timeout=30)
    assert resp.get("success") is True
    data = resp.get("data")
    assert data is not None
    assert data.get("id") == 146862
    assert "filter" in data and isinstance(data["filter"], str)
    assert "createdAt" in data


def test_get_by_filter_com_id_retorna_estrutura_general():
    """get_by_filter(146862) retorna a mesma estrutura que GET /general (data.list)."""
    resultado = comexstat.get_by_filter(146862, timeout=90)
    assert isinstance(resultado, dict)
    assert resultado.get("success") is True
    lista = _extrair_lista(resultado)
    assert isinstance(lista, list), "get_by_filter deve devolver resposta com data.list"
    assert len(lista) > 0


def test_get_by_filter_com_url_extrai_id_e_retorna_dados():
    """get_by_filter(URL com /geral/146862) extrai o ID e retorna dados."""
    url = "https://comexstat.mdic.gov.br/pt/geral/146862"
    resultado = comexstat.get_by_filter(url, timeout=90)
    assert isinstance(resultado, dict)
    assert resultado.get("success") is True
    lista = _extrair_lista(resultado)
    assert isinstance(lista, list) and len(lista) > 0
