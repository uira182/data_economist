import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_economist.regressao import (
    RegResult,
    NLSResult,
    StepwiseResult,
    ThresholdResult,
    ols,
    wls,
    robusta,
    quantilica,
    vif,
    nls,
    stepwise,
    pdl,
    ardl,
    tar,
    setar,
    star,
    coeficientes_padronizados,
    elasticidades,
)


@pytest.fixture(scope="module")
def dados_base():
    rng = np.random.default_rng(10)
    n = 140
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    y = 2.0 + 3.0 * x1 - 1.5 * x2 + rng.normal(scale=0.6, size=n)
    idx = pd.date_range("2010-01-01", periods=n, freq="ME")
    return pd.Series(y, index=idx), pd.DataFrame({"x1": x1, "x2": x2}, index=idx)


def test_ols_tipo(dados_base):
    y, X = dados_base
    r = ols(y, X)
    assert isinstance(r, RegResult)
    assert "x1" in r.params.index
    assert "beta_padronizado" in r.extras
    assert "elasticidade_media" in r.extras
    assert "variancia_coef" in r.extras


def test_wls_tipo(dados_base):
    y, X = dados_base
    w = np.linspace(1, 2, len(y))
    r = wls(y, X, weights=w)
    assert isinstance(r, RegResult)


def test_robusta_tipo(dados_base):
    y, X = dados_base
    r = robusta(y, X, m="huber")
    assert isinstance(r, RegResult)


def test_quantilica_tipo(dados_base):
    y, X = dados_base
    r = quantilica(y, X, q=0.5)
    assert isinstance(r, RegResult)
    assert r.extras["q"] == 0.5


def test_vif_saida(dados_base):
    _, X = dados_base
    out = vif(X)
    assert isinstance(out, pd.Series)
    assert "x1" in out.index


def test_nls_tipo():
    rng = np.random.default_rng(1)
    x = np.linspace(0, 4, 120)
    y = 1.5 * np.exp(0.4 * x) + rng.normal(scale=0.15, size=len(x))

    def f(xx, a, b):
        return a * np.exp(b * xx)

    r = nls(y=y, x=x, func=f, p0=[1.0, 0.2])
    assert isinstance(r, NLSResult)
    assert len(r.params) == 2


def test_stepwise_tipo(dados_base):
    y, X = dados_base
    r = stepwise(y, X, metodo="both", criterio="aic")
    assert isinstance(r, StepwiseResult)
    assert len(r.selecionadas) >= 1


def test_pdl_tipo():
    rng = np.random.default_rng(20)
    n = 140
    x = pd.Series(rng.normal(size=n))
    y = 1.0 + 0.7 * x.shift(0).fillna(0) + 0.2 * x.shift(1).fillna(0) + rng.normal(scale=0.5, size=n)
    r = pdl(y, x, lags=3, grau=2)
    assert isinstance(r, RegResult)
    assert "coef_lags" in r.extras


def test_ardl_tipo():
    rng = np.random.default_rng(30)
    n = 180
    x = rng.normal(size=n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.6 * y[t - 1] + 0.8 * x[t - 1] + rng.normal(scale=0.5)
    idx = pd.date_range("2005-01-01", periods=n, freq="ME")
    ys = pd.Series(y, index=idx)
    X = pd.DataFrame({"x": x}, index=idx)
    r = ardl(ys, X, lags_y=1, lags_x=1)
    assert isinstance(r, RegResult)


def test_tar_setar_tipo():
    rng = np.random.default_rng(40)
    n = 220
    y = np.zeros(n)
    for t in range(1, n):
        phi = 0.3 if y[t - 1] <= 0 else 0.8
        y[t] = phi * y[t - 1] + rng.normal(scale=0.4)
    ys = pd.Series(y)
    r1 = tar(ys, lag=1)
    r2 = setar(ys, lag=1)
    assert isinstance(r1, ThresholdResult)
    assert isinstance(r2, ThresholdResult)


def test_star_tipo():
    rng = np.random.default_rng(41)
    n = 220
    y = np.zeros(n)
    for t in range(1, n):
        g = 1 / (1 + np.exp(-8 * (y[t - 1] - 0.0)))
        phi = 0.2 + 0.6 * g
        y[t] = phi * y[t - 1] + rng.normal(scale=0.35)
    r = star(pd.Series(y), lag=1)
    assert isinstance(r, RegResult)
    assert "gamma" in r.extras
    assert "c" in r.extras


def test_helpers_coef_e_elasticidade(dados_base):
    y, X = dados_base
    r = ols(y, X)
    b = coeficientes_padronizados(y, pd.concat([pd.Series(1.0, index=X.index, name="const"), X], axis=1), r.params)
    e = elasticidades(y, pd.concat([pd.Series(1.0, index=X.index, name="const"), X], axis=1), r.params)
    assert isinstance(b, pd.Series)
    assert isinstance(e, pd.Series)

