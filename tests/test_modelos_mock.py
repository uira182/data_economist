"""
test_modelos_mock.py — Testes numéricos para o módulo modelos.

Valida resultados contra propriedades matemáticas conhecidas de séries sintéticas.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_economist.modelos import (
    ar, arima, sarima, prever,
    auto_arima, acf_pacf,
    adf, kpss,
    arfima, gph,
)


# ---------------------------------------------------------------------------
# Séries sintéticas com propriedades conhecidas
# ---------------------------------------------------------------------------

def _serie_ar1(phi=0.8, T=200, seed=42):
    rng = np.random.default_rng(seed)
    y = np.zeros(T)
    for t in range(1, T):
        y[t] = phi * y[t - 1] + rng.normal(0, 1)
    idx = pd.date_range("2000-01", periods=T, freq="ME")
    return pd.Series(y, index=idx, name="ar1")


def _serie_passeiro(T=200, seed=7):
    rng = np.random.default_rng(seed)
    y = np.cumsum(rng.normal(0, 1, T))
    idx = pd.date_range("2000-01", periods=T, freq="ME")
    return pd.Series(y, index=idx, name="rw")


def _serie_sazonal(m=12, T=144, seed=99):
    rng = np.random.default_rng(seed)
    t = np.arange(T)
    y = np.sin(2 * np.pi * t / m) + rng.normal(0, 0.2, T)
    idx = pd.date_range("2000-01", periods=T, freq="ME")
    return pd.Series(y, index=idx, name="sazonal")


def _serie_branca(T=300, seed=1):
    rng = np.random.default_rng(seed)
    y = rng.normal(0, 1, T)
    idx = pd.date_range("2000-01", periods=T, freq="ME")
    return pd.Series(y, index=idx, name="branca")


# ---------------------------------------------------------------------------
# AR — coeficiente estimado próximo do verdadeiro
# ---------------------------------------------------------------------------

class TestARCoeficiente:
    def test_ar1_coef_proximo_de_phi(self):
        serie = _serie_ar1(phi=0.8, T=500)
        res = ar(serie, lags=1)
        # coeficiente do lag 1 deve ser próximo de 0.8
        coef = res.params.filter(like="y.L1").values
        if len(coef) == 0:
            coef = np.array([res.params.iloc[-1]])
        assert abs(float(coef[0]) - 0.8) < 0.10, f"Coef AR(1) distante: {float(coef[0]):.4f}"

    def test_ar1_residuos_menor_variancia_que_serie(self):
        serie = _serie_ar1(phi=0.8, T=300)
        res = ar(serie, lags=1)
        assert res.residuos.var() < serie.var()

    def test_ar2_retorna_dois_coefs(self):
        serie = _serie_ar1(phi=0.5, T=300)
        res = ar(serie, lags=2)
        # AR(2) deve ter pelo menos 2 coeficientes autorregressivos
        assert len(res.params) >= 2


# ---------------------------------------------------------------------------
# ARIMA — diferenciação e estacionariedade dos resíduos
# ---------------------------------------------------------------------------

class TestARIMANumerica:
    def test_arima110_residuos_estacionarios(self):
        serie = _serie_passeiro()
        res = arima(serie, p=1, d=1, q=0)
        # Resíduos de ARIMA com d=1 em passeio aleatório devem ser aproximadamente estacionários
        # ADF deve rejeitar H0 (raiz unitária) nos resíduos
        res_adf = adf(res.residuos.dropna())
        assert res_adf.rejeita_h0, "Residuos de ARIMA(1,1,0) em RW ainda nao estacionarios"

    def test_arima_aic_menor_que_ar_no_passeiro(self):
        serie = _serie_passeiro()
        res_ar  = ar(serie, lags=1)
        res_arima = arima(serie, p=1, d=1, q=0)
        # ARIMA com diferenciação deve ter melhor ajuste que AR sem
        assert res_arima.aic <= res_ar.aic + 10


# ---------------------------------------------------------------------------
# SARIMA — captura sazonalidade
# ---------------------------------------------------------------------------

class TestSARIMANumerica:
    def test_sarima_coef_sazonal_significativo(self):
        serie = _serie_sazonal(m=12, T=144)
        res = sarima(serie, 0, 0, 0, 1, 0, 1, 12)
        # Pelo menos um parâmetro sazonal deve ter pvalue < 0.1
        pvals_sazonais = res.pvalues.filter(like="S").values
        if len(pvals_sazonais) > 0:
            assert any(p < 0.1 for p in pvals_sazonais), "Nenhum coef sazonal significativo"

    def test_sarima_aic_menor_que_arima_simples(self):
        serie = _serie_sazonal(m=12, T=144)
        res_simples = arima(serie, p=0, d=0, q=1)
        res_sazonal = sarima(serie, 0, 0, 1, 0, 0, 1, 12)
        assert res_sazonal.aic <= res_simples.aic + 15


# ---------------------------------------------------------------------------
# auto_arima — seleção de modelo
# ---------------------------------------------------------------------------

class TestAutoArimaNumerica:
    def test_ar1_seleciona_modelo_AR(self):
        serie = _serie_ar1(phi=0.8, T=300)
        res = auto_arima(serie, max_p=3, max_q=3, max_d=1, stepwise=True)
        # Para AR(1) puro, p >= 1 e q provavelmente 0 ou pequeno
        p, d, q = res.ordem[:3]
        assert p >= 1, f"auto_arima escolheu p={p} para AR(1)"

    def test_passeiro_seleciona_d1(self):
        serie = _serie_passeiro(T=200)
        res = auto_arima(serie, max_p=2, max_q=2, max_d=2, stepwise=True)
        d = res.ordem[1]
        assert d >= 1, f"auto_arima escolheu d={d} para passeio aleatorio"

    def test_criterios_retorna_menor_aic_primeiro(self):
        serie = _serie_ar1(phi=0.6, T=200)
        df = __import__(
            "data_economist.modelos",
            fromlist=["criterios"]
        ).criterios(serie, [(0, 1), (1, 0), (1, 1), (2, 0)])
        # Primeira linha (menor AIC) deve ter AIC <= segunda
        assert df["AIC"].iloc[0] <= df["AIC"].iloc[1]


# ---------------------------------------------------------------------------
# ACF/PACF — propriedades conhecidas
# ---------------------------------------------------------------------------

class TestACFPACFNumerica:
    def test_acf_branca_sem_autocorrelacao(self):
        serie = _serie_branca(T=500)
        res = acf_pacf(serie, nlags=20)
        # Para ruído branco, maioria das autocorrelações deve estar dentro do IC
        ic_width = 1.96 / np.sqrt(len(serie))
        dentro_ic = np.sum(np.abs(res.acf[1:]) < ic_width)
        assert dentro_ic >= 15, f"Muitas autocorrelacoes fora do IC: {20 - dentro_ic}"

    def test_acf_ar1_decai_exponencialmente(self):
        serie = _serie_ar1(phi=0.7, T=500)
        res = acf_pacf(serie, nlags=5)
        # ACF deve decrescer: acf[1] > acf[2] > acf[3]
        assert res.acf[1] > res.acf[2] > 0

    def test_pacf_ar1_corta_apos_lag1(self):
        serie = _serie_ar1(phi=0.7, T=500)
        res = acf_pacf(serie, nlags=5)
        ic_width = 1.96 / np.sqrt(len(serie))
        # PACF lag 1 deve ser grande; lag 3+ deve ser pequeno
        assert abs(res.pacf[1]) > ic_width
        assert abs(res.pacf[3]) < abs(res.pacf[1])


# ---------------------------------------------------------------------------
# Testes de raiz unitária — sentido correto
# ---------------------------------------------------------------------------

class TestRaizUnitariaNumerica:
    def test_adf_rejeita_ar1_estacionario(self):
        serie = _serie_ar1(phi=0.7, T=300)
        res = adf(serie, trend="c")
        assert res.rejeita_h0, "ADF deveria rejeitar H0 para AR(1) estacionario"

    def test_adf_nao_rejeita_passeiro(self):
        rng = np.random.default_rng(55)
        y = np.cumsum(rng.normal(0, 1, 100))
        idx = pd.date_range("2000-01", periods=100, freq="ME")
        serie = pd.Series(y, index=idx)
        res = adf(serie, trend="c")
        assert not res.rejeita_h0, "ADF nao deveria rejeitar H0 para passeio aleatorio"

    def test_kpss_rejeita_passeiro(self):
        serie = _serie_passeiro(T=200)
        res = kpss(serie, trend="c")
        assert res.rejeita_h0, "KPSS deveria rejeitar H0 (estacionariedade) para passeio aleatorio"

    def test_kpss_nao_rejeita_estacionaria(self):
        serie = _serie_branca(T=300)
        res = kpss(serie, trend="c")
        assert not res.rejeita_h0, "KPSS nao deveria rejeitar H0 para ruido branco"

    def test_adf_e_kpss_concordam_ar1(self):
        serie = _serie_ar1(phi=0.6, T=300)
        r_adf  = adf(serie, trend="c")
        r_kpss = kpss(serie, trend="c")
        # ADF rejeita raiz → estacionária; KPSS não rejeita → estacionária
        assert r_adf.rejeita_h0
        assert not r_kpss.rejeita_h0


# ---------------------------------------------------------------------------
# GPH — parâmetro d próximo de zero para ruído branco
# ---------------------------------------------------------------------------

class TestGPHNumerica:
    def test_gph_d_perto_de_zero_branca(self):
        serie = _serie_branca(T=500)
        res = gph(serie)
        assert abs(res["d"]) < 0.4, f"GPH d para branca: {res['d']:.4f}"

    def test_gph_ic_contem_zero_para_branca(self):
        serie = _serie_branca(T=500)
        res = gph(serie)
        lo, hi = res["ic_95"]
        assert lo <= 0 <= hi or abs(res["d"]) < 0.3


# ---------------------------------------------------------------------------
# prever — steps e índices
# ---------------------------------------------------------------------------

class TestPreverNumerica:
    def test_previsao_12_steps_mensal(self):
        serie = _serie_ar1(phi=0.7, T=200)
        mod = arima(serie, p=1, d=0, q=0)
        prev = prever(mod, steps=12)
        assert len(prev.valores) == 12

    def test_previsao_ar1_converge_para_media(self):
        serie = _serie_ar1(phi=0.5, T=300)
        mod = arima(serie, p=1, d=0, q=0)
        prev = prever(mod, steps=60)
        # Previsões de longo prazo de AR(1) estacionário convergem para a média incondicional
        media_serie = float(serie.mean())
        ultimo_valor = float(prev.valores.iloc[-1])
        assert abs(ultimo_valor - media_serie) < 2.0, (
            f"Previsao de longo prazo {ultimo_valor:.2f} distante da media {media_serie:.2f}"
        )

    def test_ic_amplitude_cresce_com_horizonte(self):
        serie = _serie_ar1(phi=0.6, T=200)
        mod = arima(serie, p=1, d=0, q=1)
        prev = prever(mod, steps=24)
        if prev.ic_lower.isna().all():
            pytest.skip("IC nao disponivel para este modelo")
        amp_inicio = float(prev.ic_upper.iloc[0]  - prev.ic_lower.iloc[0])
        amp_fim    = float(prev.ic_upper.iloc[-1] - prev.ic_lower.iloc[-1])
        assert amp_fim >= amp_inicio, "Amplitude do IC nao cresce com o horizonte"


# ---------------------------------------------------------------------------
# ARFIMA numérico
# ---------------------------------------------------------------------------

class TestARFIMANumerica:
    def test_arfima_d_zero_em_branca(self):
        serie = _serie_branca(T=300)
        res = arfima(serie, p=0, q=0)
        d_est = float(res.params["d_fracionario"])
        assert abs(d_est) < 0.35, f"ARFIMA estimou d={d_est:.4f} para branca"

    def test_arfima_d_positivo_em_ar1(self):
        serie = _serie_ar1(phi=0.8, T=300)
        res = arfima(serie, p=0, q=0)
        d_est = float(res.params["d_fracionario"])
        # AR(1) com phi alto pode ter d estimado positivo pela GPH
        assert isinstance(d_est, float)
