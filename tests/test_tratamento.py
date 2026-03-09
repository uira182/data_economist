"""
Testes do módulo tratamento: filtros, suavização, conversão de frequência e whitening.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_economist.tratamento import (
    FilterResult,
    SmoothResult,
    WhiteResult,
    bk,
    cf,
    ciclo,
    des,
    ets,
    forecast,
    holt,
    holt_winters,
    hp,
    para_frequencia,
    serie_branca,
    ses,
    suavizado,
    tendencia,
    whitening,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def serie_mensal():
    """Série mensal sintética com tendência e sazonalidade (72 obs, 2015–2020)."""
    idx = pd.date_range("2015-01", periods=72, freq="ME")
    valores = [
        100 + i * 0.5 + 10 * (1 if i % 12 in (5, 6, 7) else (-3 if i % 12 in (11, 0, 1) else 0))
        for i in range(72)
    ]
    return pd.Series(valores, index=idx, name="serie_teste", dtype=float)


@pytest.fixture
def serie_trimestral():
    """Série trimestral sintética (24 obs, 2015–2020)."""
    idx = pd.date_range("2015-01", periods=24, freq="QE")
    valores = [200 + i * 1.2 + 5 * (1 if i % 4 in (1, 2) else -2) for i in range(24)]
    return pd.Series(valores, index=idx, name="serie_trim", dtype=float)


@pytest.fixture
def serie_diaria():
    """Série diária sintética (365 obs, 2020)."""
    idx = pd.date_range("2020-01-01", periods=365, freq="D")
    valores = [50 + i * 0.05 for i in range(365)]
    return pd.Series(valores, index=idx, name="serie_diaria", dtype=float)


@pytest.fixture
def serie_sem_indice():
    """Série sem DatetimeIndex (RangeIndex) — deve levantar ValueError."""
    return pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])


# ---------------------------------------------------------------------------
# Filtro HP
# ---------------------------------------------------------------------------

def test_hp_retorna_filter_result(serie_mensal):
    resultado = hp(serie_mensal)
    assert isinstance(resultado, FilterResult)
    assert resultado.metodo == "hp"


def test_hp_tendencia_e_ciclo_preenchidos(serie_mensal):
    resultado = hp(serie_mensal)
    assert resultado.tendencia is not None
    assert resultado.ciclo is not None


def test_hp_tamanho_igual_entrada(serie_mensal):
    resultado = hp(serie_mensal)
    assert len(resultado.tendencia) == len(serie_mensal)
    assert len(resultado.ciclo) == len(serie_mensal)


def test_hp_lambda_inferido_mensal(serie_mensal):
    resultado = hp(serie_mensal)
    assert resultado.params["lamb"] == 14400


def test_hp_lambda_inferido_trimestral(serie_trimestral):
    resultado = hp(serie_trimestral)
    assert resultado.params["lamb"] == 1600


def test_hp_lambda_customizado(serie_mensal):
    resultado = hp(serie_mensal, lamb=100)
    assert resultado.params["lamb"] == 100


def test_hp_extratoras(serie_mensal):
    resultado = hp(serie_mensal)
    assert tendencia(resultado) is resultado.tendencia
    assert ciclo(resultado) is resultado.ciclo


def test_hp_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        hp(serie_sem_indice)


# ---------------------------------------------------------------------------
# Filtro BK
# ---------------------------------------------------------------------------

def test_bk_retorna_filter_result(serie_mensal):
    resultado = bk(serie_mensal, K=6)
    assert isinstance(resultado, FilterResult)
    assert resultado.metodo == "bk"


def test_bk_ciclo_mais_curto_que_entrada(serie_mensal):
    K = 6
    resultado = bk(serie_mensal, K=K)
    assert len(resultado.ciclo) == len(serie_mensal) - 2 * K


def test_bk_tendencia_none(serie_mensal):
    resultado = bk(serie_mensal, K=6)
    assert resultado.tendencia is None


def test_bk_params_corretos(serie_mensal):
    resultado = bk(serie_mensal, low=3, high=24, K=6)
    assert resultado.params["low"] == 3
    assert resultado.params["high"] == 24
    assert resultado.params["K"] == 6


def test_bk_erro_serie_curta(serie_mensal):
    serie_curta = serie_mensal.iloc[:5]
    with pytest.raises(ValueError):
        bk(serie_curta, K=6)


def test_bk_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        bk(serie_sem_indice)


# ---------------------------------------------------------------------------
# Filtro CF
# ---------------------------------------------------------------------------

def test_cf_retorna_filter_result(serie_mensal):
    resultado = cf(serie_mensal)
    assert isinstance(resultado, FilterResult)
    assert resultado.metodo == "cf"


def test_cf_ciclo_preenchido(serie_mensal):
    resultado = cf(serie_mensal)
    assert resultado.ciclo is not None
    assert len(resultado.ciclo) == len(serie_mensal)


def test_cf_asimetrico_preserva_tamanho(serie_mensal):
    resultado = cf(serie_mensal, symmetric=False)
    assert len(resultado.ciclo) == len(serie_mensal)


def test_cf_simetrico(serie_mensal):
    resultado = cf(serie_mensal, symmetric=True)
    assert resultado.ciclo is not None


def test_cf_sem_drift(serie_mensal):
    resultado = cf(serie_mensal, drift=False)
    assert resultado.params["drift"] is False


def test_cf_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        cf(serie_sem_indice)


# ---------------------------------------------------------------------------
# Suavização Exponencial Simples (SES)
# ---------------------------------------------------------------------------

def test_ses_retorna_smooth_result(serie_mensal):
    resultado = ses(serie_mensal)
    assert isinstance(resultado, SmoothResult)
    assert resultado.metodo == "ses"


def test_ses_suavizado_mesmo_tamanho(serie_mensal):
    resultado = ses(serie_mensal)
    assert len(resultado.suavizado) == len(serie_mensal)


def test_ses_alpha_estimado_automaticamente(serie_mensal):
    resultado = ses(serie_mensal)
    assert resultado.alpha is not None
    assert 0 < resultado.alpha < 1


def test_ses_alpha_fixo(serie_mensal):
    resultado = ses(serie_mensal, alpha=0.3)
    assert abs(resultado.alpha - 0.3) < 1e-6


def test_ses_beta_none(serie_mensal):
    resultado = ses(serie_mensal)
    assert resultado.beta is None
    assert resultado.gamma is None


def test_ses_extratora_suavizado(serie_mensal):
    resultado = ses(serie_mensal)
    assert suavizado(resultado) is resultado.suavizado


def test_ses_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        ses(serie_sem_indice)


# ---------------------------------------------------------------------------
# Suavização Exponencial Dupla (DES)
# ---------------------------------------------------------------------------

def test_des_retorna_smooth_result(serie_mensal):
    resultado = des(serie_mensal)
    assert isinstance(resultado, SmoothResult)
    assert resultado.metodo == "des"


def test_des_alpha_e_beta_preenchidos(serie_mensal):
    resultado = des(serie_mensal)
    assert resultado.alpha is not None
    assert resultado.beta is not None


def test_des_suavizado_mesmo_tamanho(serie_mensal):
    resultado = des(serie_mensal)
    assert len(resultado.suavizado) == len(serie_mensal)


# ---------------------------------------------------------------------------
# Holt
# ---------------------------------------------------------------------------

def test_holt_retorna_smooth_result(serie_mensal):
    resultado = holt(serie_mensal)
    assert isinstance(resultado, SmoothResult)
    assert resultado.metodo == "holt"


def test_holt_alpha_e_beta_preenchidos(serie_mensal):
    resultado = holt(serie_mensal)
    assert resultado.alpha is not None
    assert resultado.beta is not None


def test_holt_sem_amortecimento(serie_mensal):
    resultado = holt(serie_mensal, damped=False)
    assert resultado.params["damped"] is False


def test_holt_com_amortecimento(serie_mensal):
    resultado = holt(serie_mensal, damped=True)
    assert resultado.params["damped"] is True


def test_holt_suavizado_mesmo_tamanho(serie_mensal):
    resultado = holt(serie_mensal)
    assert len(resultado.suavizado) == len(serie_mensal)


def test_holt_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        holt(serie_sem_indice)


# ---------------------------------------------------------------------------
# Holt-Winters
# ---------------------------------------------------------------------------

def test_holt_winters_aditivo(serie_mensal):
    resultado = holt_winters(serie_mensal, seasonal="add")
    assert isinstance(resultado, SmoothResult)
    assert resultado.metodo == "holt_winters"
    assert resultado.params["seasonal"] == "add"


def test_holt_winters_multiplicativo(serie_mensal):
    resultado = holt_winters(serie_mensal, seasonal="mul")
    assert resultado.params["seasonal"] == "mul"


def test_holt_winters_m_inferido_mensal(serie_mensal):
    resultado = holt_winters(serie_mensal)
    assert resultado.params["m"] == 12


def test_holt_winters_m_inferido_trimestral(serie_trimestral):
    resultado = holt_winters(serie_trimestral)
    assert resultado.params["m"] == 4


def test_holt_winters_alpha_beta_gamma_preenchidos(serie_mensal):
    resultado = holt_winters(serie_mensal)
    assert resultado.alpha is not None
    assert resultado.beta is not None
    assert resultado.gamma is not None


def test_holt_winters_suavizado_mesmo_tamanho(serie_mensal):
    resultado = holt_winters(serie_mensal)
    assert len(resultado.suavizado) == len(serie_mensal)


def test_holt_winters_seasonal_invalido(serie_mensal):
    with pytest.raises(ValueError, match="seasonal"):
        holt_winters(serie_mensal, seasonal="xyz")


def test_holt_winters_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        holt_winters(serie_sem_indice)


# ---------------------------------------------------------------------------
# ETS
# ---------------------------------------------------------------------------

def test_ets_auto_retorna_smooth_result(serie_mensal):
    resultado = ets(serie_mensal)
    assert isinstance(resultado, SmoothResult)
    assert resultado.metodo == "ets"


def test_ets_auto_retorna_aic(serie_mensal):
    resultado = ets(serie_mensal)
    assert resultado.aic is not None
    assert isinstance(resultado.aic, float)


def test_ets_suavizado_mesmo_tamanho(serie_mensal):
    resultado = ets(serie_mensal)
    assert len(resultado.suavizado) == len(serie_mensal)


def test_ets_manual_sem_sazonalidade(serie_mensal):
    resultado = ets(serie_mensal, auto=False, error="add", trend="add", seasonal=None)
    assert resultado.metodo == "ets"


def test_ets_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        ets(serie_sem_indice)


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

def test_forecast_ses_retorna_serie(serie_mensal):
    resultado = ses(serie_mensal)
    prev = forecast(resultado, steps=6)
    assert isinstance(prev, pd.Series)
    assert len(prev) == 6


def test_forecast_holt_winters_retorna_serie(serie_mensal):
    resultado = holt_winters(serie_mensal)
    prev = forecast(resultado, steps=12)
    assert len(prev) == 12


def test_forecast_datas_apos_ultima_obs(serie_mensal):
    resultado = ses(serie_mensal)
    prev = forecast(resultado, steps=3)
    assert prev.index.min() > serie_mensal.index.max()


# ---------------------------------------------------------------------------
# Conversão de frequência
# ---------------------------------------------------------------------------

def test_para_frequencia_mensal_para_trimestral(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="QE", metodo="mean")
    assert isinstance(resultado, pd.Series)
    assert len(resultado) < len(serie_mensal)


def test_para_frequencia_mensal_para_anual(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="YE", metodo="mean")
    assert len(resultado) <= 6


def test_para_frequencia_metodo_sum(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="QE", metodo="sum")
    assert isinstance(resultado, pd.Series)


def test_para_frequencia_metodo_first(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="QE", metodo="first")
    assert isinstance(resultado, pd.Series)


def test_para_frequencia_metodo_last(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="QE", metodo="last")
    assert isinstance(resultado, pd.Series)


def test_para_frequencia_metodo_max(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="QE", metodo="max")
    assert isinstance(resultado, pd.Series)


def test_para_frequencia_metodo_min(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="QE", metodo="min")
    assert isinstance(resultado, pd.Series)


def test_para_frequencia_diario_para_mensal(serie_diaria):
    resultado = para_frequencia(serie_diaria, freq="ME", metodo="mean")
    assert isinstance(resultado, pd.Series)
    assert len(resultado) < len(serie_diaria)


def test_para_frequencia_mensal_para_diario_linear(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="D", metodo="linear")
    assert isinstance(resultado, pd.Series)
    assert len(resultado) > len(serie_mensal)


def test_para_frequencia_mensal_para_diario_ffill(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="D", metodo="ffill")
    assert isinstance(resultado, pd.Series)
    assert len(resultado) > len(serie_mensal)


def test_para_frequencia_retorna_serie_pandas(serie_mensal):
    resultado = para_frequencia(serie_mensal, freq="QE")
    assert isinstance(resultado, pd.Series)
    assert isinstance(resultado.index, pd.DatetimeIndex)


def test_para_frequencia_metodo_invalido(serie_mensal):
    with pytest.raises(ValueError, match="metodo"):
        para_frequencia(serie_mensal, freq="QE", metodo="xyz")


def test_para_frequencia_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        para_frequencia(serie_sem_indice, freq="QE")


# ---------------------------------------------------------------------------
# Whitening
# ---------------------------------------------------------------------------

def test_whitening_retorna_white_result(serie_mensal):
    resultado = whitening(serie_mensal)
    assert isinstance(resultado, WhiteResult)


def test_whitening_serie_branca_preenchida(serie_mensal):
    resultado = whitening(serie_mensal)
    assert resultado.serie_branca is not None
    assert isinstance(resultado.serie_branca, pd.Series)


def test_whitening_lags_positivo(serie_mensal):
    resultado = whitening(serie_mensal)
    assert resultado.lags_usados >= 1


def test_whitening_lags_fixo(serie_mensal):
    resultado = whitening(serie_mensal, lags=3)
    assert resultado.lags_usados == 3


def test_whitening_coeficientes_preenchidos(serie_mensal):
    resultado = whitening(serie_mensal)
    assert len(resultado.coeficientes) >= 1


def test_whitening_aic_float(serie_mensal):
    resultado = whitening(serie_mensal)
    assert isinstance(resultado.aic, float)


def test_whitening_extratora(serie_mensal):
    resultado = whitening(serie_mensal)
    assert serie_branca(resultado) is resultado.serie_branca


def test_whitening_residuos_menores_que_original(serie_mensal):
    resultado = whitening(serie_mensal)
    assert len(resultado.serie_branca) <= len(serie_mensal)


def test_whitening_criterio_bic(serie_mensal):
    resultado = whitening(serie_mensal, criterio="bic")
    assert resultado.params["criterio"] == "bic"


def test_whitening_criterio_invalido(serie_mensal):
    with pytest.raises(ValueError, match="criterio"):
        whitening(serie_mensal, criterio="xyz")


def test_whitening_erro_sem_datetimeindex(serie_sem_indice):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        whitening(serie_sem_indice)


# ---------------------------------------------------------------------------
# Integração — fluxo completo
# ---------------------------------------------------------------------------

def test_fluxo_hp_depois_whitening(serie_mensal):
    """Ciclo do HP pode ser branqueado antes de análise espectral."""
    r_hp = hp(serie_mensal)
    r_w = whitening(ciclo(r_hp))
    assert isinstance(r_w, WhiteResult)


def test_fluxo_converter_depois_filtrar(serie_diaria):
    """Converter diário para mensal e depois aplicar HP."""
    mensal = para_frequencia(serie_diaria, freq="ME", metodo="mean")
    r_hp = hp(mensal)
    assert isinstance(r_hp, FilterResult)
    assert len(r_hp.tendencia) == len(mensal)


def test_fluxo_holt_winters_depois_converter(serie_mensal):
    """Suavizar mensalmente e converter para trimestral."""
    r_hw = holt_winters(serie_mensal)
    suav = suavizado(r_hw)
    trimestral = para_frequencia(suav, freq="QE", metodo="last")
    assert isinstance(trimestral, pd.Series)
    assert len(trimestral) < len(serie_mensal)
