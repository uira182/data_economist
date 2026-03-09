"""
Minimos quadrados nao lineares (NLS).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.optimize as opt
import scipy.stats as sp

from ._resultado import NLSResult


def nls(y, x, func, p0):
    """
    Ajusta y = func(x, *params) + erro via scipy.curve_fit.
    """
    y_s = pd.Series(y).astype(float)
    x_v = np.asarray(x, dtype=float)
    if x_v.ndim == 1 and len(x_v) != len(y_s):
        raise ValueError("x e y precisam do mesmo comprimento")

    ok = ~np.isnan(y_s.values)
    if x_v.ndim == 1:
        ok = ok & ~np.isnan(x_v)
        x_fit = x_v[ok]
    else:
        x_fit = x_v[..., ok]
        ok = ok & np.all(~np.isnan(x_v), axis=0)
        x_fit = x_v[..., ok]
    y_fit = y_s.values[ok]

    popt, pcov = opt.curve_fit(func, x_fit, y_fit, p0=p0, maxfev=20000)
    y_hat = func(x_fit, *popt)
    resid = y_fit - y_hat

    dof = max(1, len(y_fit) - len(popt))
    stderr = np.sqrt(np.diag(pcov))
    tvals = np.divide(popt, stderr, out=np.zeros_like(popt), where=stderr > 0)
    pvals = 2 * sp.t.sf(np.abs(tvals), df=dof)

    idx = y_s.index[ok]
    return NLSResult(
        params=pd.Series(popt, index=[f"b{i}" for i in range(len(popt))]),
        stderr=pd.Series(stderr, index=[f"b{i}" for i in range(len(popt))]),
        pvalues=pd.Series(pvals, index=[f"b{i}" for i in range(len(popt))]),
        resid=pd.Series(resid, index=idx, name="resid"),
        fitted=pd.Series(y_hat, index=idx, name="fitted"),
        rmse=float(np.sqrt(np.mean(resid**2))),
        nobs=int(len(y_fit)),
        fit_obj={"pcov": pcov},
    )

