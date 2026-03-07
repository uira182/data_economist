"""
Testes do módulo X-13 (seasonal): init, get_x13_bin_path, spec_builder, seas, final, summary, udg.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Garantir que o src está no path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_economist.x13 import (
    final,
    get_series,
    get_x13_bin_path,
    init,
    irregular,
    original,
    seas,
    summary,
    trend,
    udg,
)
from data_economist.x13.spec_builder import build_spec
from data_economist.x13.seas import SeasonalResult


# ---- init e get_x13_bin_path ----
def test_init_returns_venv_path():
    """init() devolve o Path do diretório venv."""
    root = Path(__file__).resolve().parents[1]
    venv_path = init(project_root=root)
    assert venv_path.is_dir()
    assert venv_path.name == "venv"


def test_get_x13_bin_path_returns_string():
    """get_x13_bin_path() devolve caminho do executável."""
    root = Path(__file__).resolve().parents[1]
    path = get_x13_bin_path(project_root=root)
    assert isinstance(path, str)
    assert "x13" in path.lower() or "x13as" in path.lower()
    assert Path(path).is_file()


# ---- spec_builder ----
def test_build_spec_produces_series_block():
    """build_spec() gera conteúdo .spc com bloco series e data."""
    idx = pd.date_range("2020-01", periods=24, freq="ME")
    s = pd.Series(range(100, 124), index=idx)
    content = build_spec(s, title="test")
    assert "series{" in content
    assert "title=" in content
    assert "start=2020.01" in content
    assert "data=(" in content
    assert "100" in content
    assert "transform{" in content


def test_build_spec_arima_model_without_double_parentheses():
    """arima_model não deve gerar parênteses duplicados no .spc."""
    idx = pd.date_range("2020-01", periods=24, freq="ME")
    s = pd.Series(range(100, 124), index=idx)
    content = build_spec(s, title="test", automdl=False, arima_model="(1 0 1)(1 0 1)")
    assert "arima{" in content
    assert "model=(1 0 1)(1 0 1)" in content
    assert "model=((1 0 1)(1 0 1))" not in content


# ---- seas (requer binário X-13) ----
@pytest.fixture
def monthly_series():
    """Série mensal com padrão sazonal (evitar 'differencing annihilated')."""
    idx = pd.date_range("2012-01", periods=60, freq="ME")
    import numpy as np
    np.random.seed(42)
    trend = np.linspace(100, 115, 60)
    seasonal = 5 * np.sin(2 * np.pi * np.arange(60) / 12)
    return pd.Series(trend + seasonal + np.random.normal(0, 1, 60), index=idx)


def test_seas_returns_seasonal_result(monthly_series):
    """seas(series) devolve SeasonalResult com original e final."""
    model = seas(monthly_series, title="pytest")
    assert isinstance(model, SeasonalResult)
    assert len(model.original) == len(monthly_series)
    assert len(model.final) == len(monthly_series)
    assert "nobs" in model.udg or "freq" in model.udg


def test_final_original_trend_irregular(monthly_series):
    """final(m), original(m), trend(m), irregular(m) devolvem séries ou None."""
    model = seas(monthly_series)
    assert final(model) is not None
    assert original(model) is not None
    assert len(original(model)) == len(monthly_series)
    assert len(final(model)) == len(monthly_series)
    # trend/irregular podem ser None se o parser não extrair do HTML
    trend(model)
    irregular(model)


def test_udg_returns_dict(monthly_series):
    """udg(model) devolve dicionário de diagnósticos."""
    model = seas(monthly_series)
    d = udg(model)
    assert isinstance(d, dict)
    assert len(d) >= 1


def test_summary_returns_string(monthly_series):
    """summary(model) devolve str com X-13 e diagnósticos."""
    model = seas(monthly_series)
    text = summary(model)
    assert isinstance(text, str)
    assert "X-13" in text or "Seasonal" in text
    assert "Original" in text or "obs" in text


def test_get_series_keys(monthly_series):
    """get_series(model, key) devolve original, final; trend/irregular podem ser None."""
    model = seas(monthly_series)
    assert get_series(model, "original") is not None
    assert get_series(model, "final") is not None
    assert get_series(model, "nonexistent") is None
