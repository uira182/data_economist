import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_economist.regressao import ols, wls, robusta, quantilica, nls, stepwise, pdl, ardl, tar, star


def test_mock_ols_recupera_coeficientes():
    rng = np.random.default_rng(100)
    n = 500
    x = rng.normal(size=n)
    y = 2.0 + 3.0 * x + rng.normal(scale=0.4, size=n)
    r = ols(y, pd.DataFrame({"x": x}))
    assert abs(r.params["const"] - 2.0) < 0.15
    assert abs(r.params["x"] - 3.0) < 0.15


def test_mock_wls_heterocedasticidade():
    rng = np.random.default_rng(101)
    n = 400
    x = rng.uniform(0.1, 2.0, size=n)
    sigma = 0.2 + x
    eps = rng.normal(scale=sigma, size=n)
    y = 1.0 + 2.0 * x + eps
    w = 1 / (sigma**2)
    r_ols = ols(y, pd.DataFrame({"x": x}))
    r_wls = wls(y, pd.DataFrame({"x": x}), weights=w)
    # Com pesos corretos, coef deve estar mais perto do verdadeiro na maioria dos casos
    assert abs(r_wls.params["x"] - 2.0) <= abs(r_ols.params["x"] - 2.0) + 0.15


def test_mock_robusta_resiste_outlier():
    rng = np.random.default_rng(102)
    n = 250
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + rng.normal(scale=0.3, size=n)
    y[0] += 25  # outlier extremo
    r_ols = ols(y, pd.DataFrame({"x": x}))
    r_rlm = robusta(y, pd.DataFrame({"x": x}))
    assert abs(r_rlm.params["x"] - 2.0) < abs(r_ols.params["x"] - 2.0) + 0.2


def test_mock_quantilica_mediana_aproxima_ols():
    rng = np.random.default_rng(103)
    n = 350
    x = rng.normal(size=n)
    y = 0.5 + 1.5 * x + rng.normal(scale=0.6, size=n)
    r_ols = ols(y, pd.DataFrame({"x": x}))
    r_q50 = quantilica(y, pd.DataFrame({"x": x}), q=0.5)
    assert abs(r_q50.params["x"] - r_ols.params["x"]) < 0.25


def test_mock_nls_exponencial():
    rng = np.random.default_rng(104)
    x = np.linspace(0, 5, 200)
    y = 1.8 * np.exp(0.35 * x) + rng.normal(scale=0.2, size=len(x))

    def f(xx, a, b):
        return a * np.exp(b * xx)

    r = nls(y=y, x=x, func=f, p0=[1.0, 0.2])
    assert abs(r.params["b0"] - 1.8) < 0.25
    assert abs(r.params["b1"] - 0.35) < 0.08


def test_mock_stepwise_seleciona_relevante():
    rng = np.random.default_rng(105)
    n = 280
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    x3 = rng.normal(size=n)
    y = 3.0 + 2.2 * x1 + rng.normal(scale=0.7, size=n)  # somente x1 relevante
    X = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})
    r = stepwise(y, X, metodo="both", criterio="aic")
    assert "x1" in r.selecionadas


def test_mock_pdl_roda_e_gera_lags():
    rng = np.random.default_rng(106)
    n = 260
    x = pd.Series(rng.normal(size=n))
    y = 1.2 + 0.9 * x + 0.4 * x.shift(1).fillna(0) + 0.1 * x.shift(2).fillna(0) + rng.normal(scale=0.6, size=n)
    r = pdl(y, x, lags=4, grau=2)
    assert "coef_lags" in r.extras
    assert len(r.extras["coef_lags"]) == 5


def test_mock_ardl_roda():
    rng = np.random.default_rng(107)
    n = 240
    x = rng.normal(size=n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.55 * y[t - 1] + 0.75 * x[t - 1] + rng.normal(scale=0.5)
    idx = pd.date_range("2000-01-01", periods=n, freq="ME")
    r = ardl(pd.Series(y, index=idx), pd.DataFrame({"x": x}, index=idx), lags_y=1, lags_x=1)
    assert r.nobs > 150


def test_mock_tar_separa_regimes():
    rng = np.random.default_rng(108)
    n = 300
    y = np.zeros(n)
    for t in range(1, n):
        phi = 0.2 if y[t - 1] < 0 else 0.85
        y[t] = phi * y[t - 1] + rng.normal(scale=0.35)
    out = tar(pd.Series(y), lag=1)
    b1 = out.resultado_regime_1.params.get("ylag", np.nan)
    b2 = out.resultado_regime_2.params.get("ylag", np.nan)
    assert b2 > b1


def test_mock_star_roda():
    rng = np.random.default_rng(109)
    n = 320
    y = np.zeros(n)
    for t in range(1, n):
        g = 1 / (1 + np.exp(-10 * (y[t - 1] - 0.1)))
        phi = 0.25 + 0.55 * g
        y[t] = phi * y[t - 1] + rng.normal(scale=0.3)
    out = star(pd.Series(y), lag=1)
    assert out.modelo.startswith("STAR")

