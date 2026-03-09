"""
Testes estruturais e mock para o módulo data_economist.fred.

Todos os testes usam respostas HTTP simuladas (unittest.mock) — sem token real nem
chamada de rede. Para testes de integração com a API real, use pytest -m integration.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

import data_economist.fred as fred
from data_economist.fred import FredError


# ---------------------------------------------------------------------------
# Fixtures de resposta mock
# ---------------------------------------------------------------------------

def _mock_response(status_code: int, body: dict | list) -> MagicMock:
    """Cria um objeto Response simulado."""
    mock = MagicMock(spec=requests.Response)
    mock.status_code = status_code
    mock.json.return_value = body
    mock.raise_for_status = MagicMock()
    return mock


def _observations_body(
    values: list[str] | None = None,
    dates: list[str] | None = None,
) -> dict:
    dates = dates or ["2024-01-01", "2024-02-01", "2024-03-01"]
    values = values or ["310.326", "311.054", "312.100"]
    return {
        "observations": [
            {"realtime_start": "2024-01-01", "realtime_end": "9999-12-31",
             "date": d, "value": v}
            for d, v in zip(dates, values)
        ]
    }


def _series_body(series_id: str = "CPIAUCSL") -> dict:
    return {
        "seriess": [{
            "id": series_id,
            "title": "Consumer Price Index",
            "frequency": "Monthly",
            "frequency_short": "M",
            "units": "Index 1982-1984=100",
            "units_short": "Index",
            "seasonal_adjustment": "Seasonally Adjusted",
            "seasonal_adjustment_short": "SA",
            "observation_start": "1947-01-01",
            "observation_end": "2024-12-01",
            "last_updated": "2024-12-11 08:01:05-06",
            "realtime_start": "2024-12-11",
            "realtime_end": "9999-12-31",
            "notes": "Frequência mensal.",
        }]
    }


def _search_body(series_id: str = "CPIAUCSL") -> dict:
    return {"seriess": [_series_body(series_id)["seriess"][0]]}


def _category_body(category_id: int = 0) -> dict:
    return {"categories": [{"id": category_id, "name": "Categories", "parent_id": 0}]}


def _tags_body() -> dict:
    return {
        "tags": [
            {"name": "bls", "group_id": "src", "notes": "Bureau of Labor Statistics",
             "created": "2012-02-27 10:01:01-06", "popularity": 100, "series_count": 4500},
            {"name": "cpi", "group_id": "gen", "notes": "",
             "created": "2012-02-27 10:01:01-06", "popularity": 98, "series_count": 300},
        ]
    }


def _release_body(release_id: int = 10) -> dict:
    return {
        "releases": [{
            "id": release_id,
            "realtime_start": "2024-01-01",
            "realtime_end": "9999-12-31",
            "name": "Employment Situation",
            "press_release": True,
            "link": "https://www.bls.gov/news.release/empsit.htm",
        }]
    }


# ---------------------------------------------------------------------------
# Helpers para patch de session
# ---------------------------------------------------------------------------

def _patch_session(status_code: int, body: dict):
    """Faz patch de requests.Session para retornar uma resposta mock."""
    mock_resp = _mock_response(status_code, body)
    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    return mock_session


# ===========================================================================
# 1. Autenticação
# ===========================================================================

class TestAutenticacao:
    def test_token_ausente_levanta_valueerror(self):
        env = {k: v for k, v in os.environ.items() if k not in ("TOKEN_FRED", "FRED_API_KEY")}
        with patch.dict(os.environ, env, clear=True):
            # neutraliza load_dotenv para o .env local nao interferir
            with patch("data_economist.fred._load_env"):
                with pytest.raises(ValueError, match="TOKEN_FRED"):
                    fred.get("CPIAUCSL")

    def test_token_via_parametro_nao_consulta_env(self):
        """api_key explícito não deve tentar ler TOKEN_FRED."""
        body = _observations_body()
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, body)
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", api_key="token_teste_123")
        assert isinstance(result, list)

    def test_status_401_levanta_valueerror(self):
        with patch("data_economist.fred._get_token", return_value="tok"):
            with patch("data_economist.fred._build_session") as mock_build:
                session = _patch_session(401, {})
                mock_build.return_value = session
                with pytest.raises(ValueError, match="invalido"):
                    fred.get("CPIAUCSL", api_key="tok_invalido")

    def test_status_403_levanta_valueerror(self):
        with patch("data_economist.fred._get_token", return_value="tok"):
            with patch("data_economist.fred._build_session") as mock_build:
                session = _patch_session(403, {})
                mock_build.return_value = session
                with pytest.raises(ValueError, match="invalido"):
                    fred.get("CPIAUCSL", api_key="tok_invalido")

    def test_json_com_error_message_api_key_levanta_valueerror(self):
        body = {"error_code": 400, "error_message": "Bad Request. Variable api_key is not one of the current api_keys."}
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, body)
            mock_build.return_value = session
            with pytest.raises(ValueError, match=r"invalido|\.env"):
                fred.get("CPIAUCSL", api_key="tok")

    def test_json_com_error_message_generico_levanta_frederror(self):
        body = {"error_code": 404, "error_message": "Not found."}
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, body)
            mock_build.return_value = session
            with pytest.raises(FredError):
                fred.get("CPIAUCSL", api_key="tok")


# ===========================================================================
# 2. fred.get — observações
# ===========================================================================

class TestGet:
    def test_retorna_lista_de_dicts(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _observations_body())
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", api_key="tok")
        assert isinstance(result, list)
        assert len(result) == 3

    def test_campos_date_e_value(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _observations_body())
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", api_key="tok")
        assert "date" in result[0]
        assert "value" in result[0]

    def test_value_e_float(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _observations_body())
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", api_key="tok")
        assert isinstance(result[0]["value"], float)

    def test_ponto_convertido_para_none(self):
        """Valor '.' deve ser convertido para None."""
        body = _observations_body(values=[".", "311.054", "."])
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, body)
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", api_key="tok")
        assert result[0]["value"] is None
        assert result[1]["value"] == pytest.approx(311.054)
        assert result[2]["value"] is None

    def test_date_como_string(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _observations_body())
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", api_key="tok")
        assert result[0]["date"] == "2024-01-01"

    def test_date_init_e_date_end_aceita_string(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _observations_body())
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", date_init="2020-01-01", date_end="2024-12-31", api_key="tok")
        assert isinstance(result, list)

    def test_date_init_aceita_datetime(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _observations_body())
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", date_init=datetime(2020, 1, 1), api_key="tok")
        assert isinstance(result, list)

    def test_date_invalida_levanta_valueerror(self):
        with pytest.raises(ValueError):
            fred.get("CPIAUCSL", date_init="01/01/2020", api_key="tok")

    def test_lista_vazia_quando_sem_observacoes(self):
        body = {"observations": []}
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, body)
            mock_build.return_value = session
            result = fred.get("CPIAUCSL", api_key="tok")
        assert result == []

    def test_status_404_levanta_frederror(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(404, {})
            mock_build.return_value = session
            with pytest.raises(FredError):
                fred.get("SERIE_INEXISTENTE", api_key="tok")

    def test_status_429_levanta_frederror(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(429, {})
            mock_build.return_value = session
            with pytest.raises(FredError, match="429"):
                fred.get("CPIAUCSL", api_key="tok")


# ===========================================================================
# 3. fred.metadados
# ===========================================================================

class TestMetadados:
    def test_retorna_dict(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _series_body())
            mock_build.return_value = session
            result = fred.metadados("CPIAUCSL", api_key="tok")
        assert isinstance(result, dict)

    def test_campos_esperados(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _series_body())
            mock_build.return_value = session
            result = fred.metadados("CPIAUCSL", api_key="tok")
        for campo in ("id", "title", "frequency", "units", "seasonal_adjustment",
                      "observation_start", "observation_end"):
            assert campo in result, f"Campo '{campo}' ausente nos metadados"

    def test_id_bate_com_series_id(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _series_body("FEDFUNDS"))
            mock_build.return_value = session
            result = fred.metadados("FEDFUNDS", api_key="tok")
        assert result["id"] == "FEDFUNDS"

    def test_serie_nao_encontrada_levanta_frederror(self):
        body = {"seriess": []}
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, body)
            mock_build.return_value = session
            with pytest.raises(FredError, match="não encontrada"):
                fred.metadados("XXX_INEXISTENTE", api_key="tok")


# ===========================================================================
# 4. fred.buscar
# ===========================================================================

class TestBuscar:
    def test_retorna_lista(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _search_body())
            mock_build.return_value = session
            result = fred.buscar("consumer price index", api_key="tok")
        assert isinstance(result, list)

    def test_item_tem_campos_de_metadados(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _search_body())
            mock_build.return_value = session
            result = fred.buscar("cpi", api_key="tok")
        assert len(result) >= 1
        assert "id" in result[0]
        assert "title" in result[0]

    def test_lista_vazia_quando_sem_resultado(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, {"seriess": []})
            mock_build.return_value = session
            result = fred.buscar("xyzabcnotexist", api_key="tok")
        assert result == []


# ===========================================================================
# 5. fred.categorias
# ===========================================================================

class TestCategorias:
    def test_retorna_dict_com_id_e_name(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _category_body(0))
            mock_build.return_value = session
            result = fred.categorias(api_key="tok")
        assert isinstance(result, dict)
        assert "id" in result
        assert "name" in result

    def test_categoria_nao_encontrada_levanta_frederror(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, {"categories": []})
            mock_build.return_value = session
            with pytest.raises(FredError):
                fred.categorias(category_id=999999, api_key="tok")


# ===========================================================================
# 6. fred.series_categoria
# ===========================================================================

class TestSeriesCategoria:
    def test_retorna_lista(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _search_body())
            mock_build.return_value = session
            result = fred.series_categoria(125, api_key="tok")
        assert isinstance(result, list)

    def test_lista_vazia_quando_sem_series(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, {"seriess": []})
            mock_build.return_value = session
            result = fred.series_categoria(125, api_key="tok")
        assert result == []


# ===========================================================================
# 7. fred.tags
# ===========================================================================

class TestTags:
    def test_retorna_lista(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _tags_body())
            mock_build.return_value = session
            result = fred.tags("CPIAUCSL", api_key="tok")
        assert isinstance(result, list)

    def test_item_tem_name(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _tags_body())
            mock_build.return_value = session
            result = fred.tags("CPIAUCSL", api_key="tok")
        assert len(result) >= 1
        assert "name" in result[0]

    def test_lista_vazia_quando_sem_tags(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, {"tags": []})
            mock_build.return_value = session
            result = fred.tags("CPIAUCSL", api_key="tok")
        assert result == []


# ===========================================================================
# 8. fred.release e fred.series_release
# ===========================================================================

class TestRelease:
    def test_release_retorna_dict(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _release_body(10))
            mock_build.return_value = session
            result = fred.release(10, api_key="tok")
        assert isinstance(result, dict)
        assert result["id"] == 10
        assert "name" in result

    def test_release_nao_encontrado_levanta_frederror(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, {"releases": []})
            mock_build.return_value = session
            with pytest.raises(FredError):
                fred.release(999999, api_key="tok")

    def test_series_release_retorna_lista(self):
        with patch("data_economist.fred._build_session") as mock_build:
            session = _patch_session(200, _search_body())
            mock_build.return_value = session
            result = fred.series_release(10, api_key="tok")
        assert isinstance(result, list)


# ===========================================================================
# 9. SERIES_FRED — constante de séries de referência
# ===========================================================================

class TestSeriesFred:
    def test_series_fred_e_dict(self):
        assert isinstance(fred.SERIES_FRED, dict)

    def test_chaves_de_frequencia(self):
        for freq in ("daily", "monthly", "quarterly"):
            assert freq in fred.SERIES_FRED

    def test_grupo_pol_mon_mensal(self):
        pol_mon = fred.SERIES_FRED["monthly"]["pol_mon"]
        assert isinstance(pol_mon, list)
        assert "CPIAUCSL" in pol_mon
        assert "FEDFUNDS" in pol_mon
        assert "UNRATE" in pol_mon

    def test_grupo_pol_mon_diario(self):
        pol_mon = fred.SERIES_FRED["daily"]["pol_mon"]
        assert "VIXCLS" in pol_mon
        assert "SP500" in pol_mon

    def test_series_sao_strings(self):
        for freq, grupos in fred.SERIES_FRED.items():
            for grupo, series in grupos.items():
                for s in series:
                    assert isinstance(s, str), f"Série não-string em {freq}/{grupo}: {s!r}"

    def test_total_series_mensais(self):
        mensais = fred.SERIES_FRED["monthly"]
        total = sum(len(v) for v in mensais.values())
        assert total >= 20, f"Esperado >= 20 séries mensais, obtido {total}"


# ===========================================================================
# 10. Importação pelo pacote principal
# ===========================================================================

class TestImportacao:
    def test_importar_pelo_pacote(self):
        import data_economist
        assert hasattr(data_economist, "fred")

    def test_fred_tem_get(self):
        import data_economist
        assert callable(data_economist.fred.get)

    def test_fred_tem_metadados(self):
        import data_economist
        assert callable(data_economist.fred.metadados)

    def test_fred_tem_buscar(self):
        import data_economist
        assert callable(data_economist.fred.buscar)

    def test_fred_tem_series_fred(self):
        import data_economist
        assert hasattr(data_economist.fred, "SERIES_FRED")

    def test_fred_tem_frederror(self):
        assert issubclass(fred.FredError, Exception)
