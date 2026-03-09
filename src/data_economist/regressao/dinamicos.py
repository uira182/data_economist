"""
Modelos dinamicos: PDL e ARDL.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._resultado import RegResult
from .linear import ols


def _pack(fit, nome):
    idx = fit.model.data.row_labels
    return RegResult(
        modelo=nome,
        params=pd.Series(fit.params),
        pvalues=pd.Series(fit.pvalues),
        aic=float(getattr(fit, "aic", np.nan)),
        bic=float(getattr(fit, "bic", np.nan)),
        r2=float(getattr(fit, "rsquared", np.nan)),
        r2_adj=float(getattr(fit, "rsquared_adj", np.nan)),
        resid=pd.Series(fit.resid, index=idx, name="resid"),
        fitted=pd.Series(fit.fittedvalues, index=idx, name="fitted"),
        nobs=int(fit.nobs),
        extras={},
        fit_obj=fit,
    )


def pdl(y, x, lags=4, grau=2, add_const=True) -> RegResult:
    """
    Polynomial Distributed Lag (Almon).
    """
    y_s = pd.Series(y).astype(float).rename("y")
    x_s = pd.Series(x).astype(float).rename("x")
    df = pd.concat([y_s, x_s], axis=1).dropna()
    y0 = df["y"]
    x0 = df["x"]

    # Regressoras Almon: Z_k(t) = sum_{j=0..L} j^k x_{t-j}
    z = {}
    for k in range(grau + 1):
        acc = None
        for j in range(lags + 1):
            term = (j**k) * x0.shift(j)
            acc = term if acc is None else (acc + term)
        z[f"z{k}"] = acc

    Z = pd.DataFrame(z)
    base = pd.concat([y0, Z], axis=1).dropna()
    res = ols(base["y"], base.drop(columns=["y"]), add_const=add_const)

    # Reconstruir coeficientes por lag
    b = []
    for j in range(lags + 1):
        bj = 0.0
        for k in range(grau + 1):
            name = f"z{k}"
            if name in res.params.index:
                bj += float(res.params[name]) * (j**k)
        b.append(bj)
    res.extras["coef_lags"] = pd.Series(b, index=[f"lag{j}" for j in range(lags + 1)])
    res.modelo = f"PDL(lags={lags},grau={grau})"
    return res


def ardl(y, X, lags_y=1, lags_x=1, trend="c") -> RegResult:
    """
    ARDL usando statsmodels.tsa.ardl.ARDL.
    """
    from statsmodels.tsa.ardl import ARDL

    y_s = pd.Series(y).astype(float).rename("y")
    X_df = pd.DataFrame(X).astype(float)
    base = pd.concat([y_s, X_df], axis=1).dropna()
    y_ok = base["y"]
    X_ok = base.drop(columns=["y"])

    fit = ARDL(y_ok, lags=lags_y, exog=X_ok, order=lags_x, trend=trend).fit()
    out = _pack(fit, f"ARDL(y={lags_y},x={lags_x})")
    return out


def ardl_bounds(resultado_ardl: RegResult):
    """
    Executa bounds test de cointegração quando disponivel no objeto fit.
    """
    fit = resultado_ardl.fit_obj
    if fit is None:
        raise ValueError("resultado sem fit_obj")

    if hasattr(fit, "bounds_test"):
        return fit.bounds_test()
    if hasattr(fit.model, "bounds_test"):
        return fit.model.bounds_test(fit.params)
    raise NotImplementedError("Bounds test nao disponivel nesta versao do statsmodels")

