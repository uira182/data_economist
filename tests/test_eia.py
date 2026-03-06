"""
Testes do módulo EIA (U.S. Energy Information Administration).

Cobre: get, get_data, get_steo, get_petroleum, get_by_landing, mapeamentos
SERIES_STEO/SERIES_PETROLEUM, token em falta e token inválido (403).
"""

import os
from unittest.mock import patch, MagicMock

import pytest

from data_economist import eia


# ---- Import e mapeamentos ----
def test_import_eia():
    """from data_economist import eia expõe get, get_data, get_steo, get_petroleum, get_by_landing e mapeamentos."""
    assert hasattr(eia, "get")
    assert hasattr(eia, "get_data")
    assert hasattr(eia, "get_steo")
    assert hasattr(eia, "get_petroleum")
    assert hasattr(eia, "get_by_landing")
    assert hasattr(eia, "SERIES_STEO")
    assert hasattr(eia, "SERIES_PETROLEUM")


# ---- Token em falta ou inválido ----
def test_missing_token_raises():
    """Sem TOKEN_EIA no ambiente e sem api_key, get() levanta ValueError."""
    url = "https://api.eia.gov/v2/steo/data/?frequency=monthly"
    with patch.dict(os.environ, {"TOKEN_EIA": "", "EIA_API_KEY": ""}, clear=False):
        with pytest.raises(ValueError) as exc_info:
            eia.get(url)
    assert "TOKEN_EIA" in str(exc_info.value) or "Token EIA" in str(exc_info.value)
    assert "eia.gov/opendata/register" in str(exc_info.value).lower()


def test_get_with_api_key_returns_structure():
    """Com api_key passado e request mockada, get() devolve o JSON da resposta."""
    url = "https://api.eia.gov/v2/steo/data/?frequency=monthly&data[0]=value&facets[seriesId][]=PATC_WORLD"
    mock_response = {
        "response": {
            "data": [
                {"period": "2024-01", "value": 100.5, "seriesId": "PATC_WORLD"},
                {"period": "2023-12", "value": 99.2, "seriesId": "PATC_WORLD"},
            ],
            "total": 2,
        }
    }
    with patch("data_economist.eia.requests.get") as m_get:
        m_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)
        result = eia.get(url, api_key="fake_token")
    assert result == mock_response
    assert "response" in result
    assert result["response"]["data"] == mock_response["response"]["data"]
    m_get.assert_called_once()
    requested_url = m_get.call_args[0][0]
    assert "api_key=" in requested_url and "fake_token" in requested_url


def test_get_data_returns_list():
    """get_data() devolve a lista em response.response.data."""
    url = "https://api.eia.gov/v2/steo/data/?frequency=monthly"
    mock_response = {
        "response": {
            "data": [
                {"period": "2024-01", "value": 100, "seriesId": "PATC_WORLD"},
            ],
        }
    }
    with patch("data_economist.eia.requests.get") as m_get:
        m_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)
        data = eia.get_data(url, api_key="fake")
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["period"] == "2024-01"
    assert data[0]["value"] == 100


def test_get_403_raises_value_error_with_doc_link():
    """Se a API devolver 403 (token inválido), levanta ValueError com link da documentação EIA."""
    url = "https://api.eia.gov/v2/steo/data/?frequency=monthly"
    with patch("data_economist.eia.requests.get") as m_get:
        m_get.return_value = MagicMock(status_code=403)
        m_get.return_value.raise_for_status.side_effect = None
        with pytest.raises(ValueError) as exc_info:
            eia.get(url, api_key="token_invalido")
    msg = str(exc_info.value)
    assert "token" in msg.lower() or "TOKEN_EIA" in msg
    assert "eia.gov/opendata" in msg.lower()
    assert "documentation" in msg.lower() or "documentação" in msg.lower()


# ---- get e get_data ----
def test_get_data_empty_response_returns_empty_list():
    """Se a API não devolver response.data, get_data() devolve lista vazia."""
    url = "https://api.eia.gov/v2/steo/data/?frequency=monthly"
    with patch("data_economist.eia.requests.get") as m_get:
        m_get.return_value = MagicMock(status_code=200, json=lambda: {"response": {}})
        data = eia.get_data(url, api_key="fake")
    assert data == []


# ---- get_steo, get_petroleum, get_by_landing ----
def test_get_steo_builds_url_and_returns_data():
    """get_steo(series_id, frequency) monta URL STEO e devolve lista via get_data."""
    mock_data = [{"period": "2024-01", "value": 80.0, "seriesId": "PATC_WORLD"}]
    with patch("data_economist.eia.get_data") as m_get_data:
        m_get_data.return_value = mock_data
        result = eia.get_steo("PATC_WORLD", "monthly", api_key="fake")
    assert result == mock_data
    m_get_data.assert_called_once()
    url = m_get_data.call_args[0][0]
    assert "/steo/data/" in url
    assert "PATC_WORLD" in url
    assert "monthly" in url


def test_get_petroleum_builds_url_and_returns_data():
    """get_petroleum(route, series, frequency) monta URL Petroleum e devolve lista."""
    mock_data = [{"period": "2024-01-15", "value": 72.5, "series": "EER_EPMRU_PF4_RGC_DPG"}]
    with patch("data_economist.eia.get_data") as m_get_data:
        m_get_data.return_value = mock_data
        result = eia.get_petroleum("pri/spt", "EER_EPMRU_PF4_RGC_DPG", "daily", api_key="fake")
    assert result == mock_data
    m_get_data.assert_called_once()
    url = m_get_data.call_args[0][0]
    assert "/petroleum/pri/spt/data/" in url
    assert "EER_EPMRU" in url
    assert "daily" in url


def test_get_by_landing_petroleo_monthly_retorna_dict_por_serie():
    """get_by_landing('petroleo', 'monthly') devolve dict com uma entrada por série STEO."""
    mock_row = [{"period": "2024-01", "value": 1, "seriesId": "PATC_WORLD"}]
    with patch("data_economist.eia.get_steo") as m_steo:
        m_steo.return_value = mock_row
        result = eia.get_by_landing("petroleo", "monthly", api_key="fake")
    assert isinstance(result, dict)
    assert set(result.keys()) == set(eia.SERIES_STEO["petroleo_monthly"])
    assert result["PATC_WORLD"] == mock_row
    assert m_steo.call_count == len(eia.SERIES_STEO["petroleo_monthly"])


def test_get_by_landing_petroleo_weekly_chama_get_petroleum():
    """get_by_landing('petroleo', 'weekly') devolve dict com uma entrada por (route, series)."""
    mock_row = [{"period": "2024-W01", "value": 100, "series": "WGFUPUS2"}]
    with patch("data_economist.eia.get_petroleum") as m_pet:
        m_pet.return_value = mock_row
        result = eia.get_by_landing("petroleo", "weekly", api_key="fake")
    assert isinstance(result, dict)
    assert len(result) == len(eia.SERIES_PETROLEUM["petroleo_weekly"])
    assert m_pet.call_count == len(eia.SERIES_PETROLEUM["petroleo_weekly"])


def test_series_steo_and_petroleum_mapping():
    """Mapeamentos SERIES_STEO e SERIES_PETROLEUM contêm as séries do landing."""
    assert "PATC_WORLD" in eia.SERIES_STEO["petroleo_monthly"]
    assert "PAPR_OPEC" in eia.SERIES_STEO["petroleo_monthly"]
    assert "NGHHUUS" in eia.SERIES_STEO["quimicos_monthly"]
    assert "ZOTOIUS" in eia.SERIES_STEO["min_sid_monthly"]
    routes_series = [r for r, _ in eia.SERIES_PETROLEUM["petroleo_daily"]]
    assert "pri/spt" in routes_series
    assert any(s == "EER_EPMRU_PF4_RGC_DPG" for _, s in eia.SERIES_PETROLEUM["petroleo_daily"])


# ---- Integração com API real (requer TOKEN_EIA no .env) ----
@pytest.mark.skipif(
    not os.environ.get("TOKEN_EIA") and not os.environ.get("EIA_API_KEY"),
    reason="TOKEN_EIA (ou EIA_API_KEY) não definido — teste de integração com API real",
)
def test_get_real_request_structure():
    """Com token no ambiente, uma requisição real à EIA devolve response com data (lista)."""
    url = (
        "https://api.eia.gov/v2/steo/data/?frequency=monthly&data[0]=value"
        "&facets[seriesId][]=PATC_WORLD&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5"
    )
    result = eia.get(url, timeout=15)
    assert isinstance(result, dict)
    assert "response" in result
    data = result.get("response", {}).get("data", [])
    assert isinstance(data, list)
    if data:
        assert "period" in data[0] and "value" in data[0]
