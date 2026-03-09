"""
Regressao de limiar (TAR / SETAR / STAR basico).
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from ._resultado import ThresholdResult
from .linear import ols


def tar(y, lag=1, threshold=None) -> ThresholdResult:
    """
    TAR simples em dois regimes:
    y_t = a1 + b1 y_{t-1} + e_t  se y_{t-lag} <= gamma
    y_t = a2 + b2 y_{t-1} + e_t  se y_{t-lag} >  gamma
    """
    y_s = pd.Series(y).astype(float).rename("y")
    df = pd.DataFrame({"y": y_s, "ylag": y_s.shift(1), "gate": y_s.shift(lag)}).dropna()
    if threshold is None:
        threshold = float(df["gate"].median())

    d1 = df[df["gate"] <= threshold]
    d2 = df[df["gate"] > threshold]
    if len(d1) < 8 or len(d2) < 8:
        raise ValueError("regimes insuficientes para estimacao TAR")

    r1 = ols(d1["y"], d1[["ylag"]], add_const=True)
    r2 = ols(d2["y"], d2[["ylag"]], add_const=True)
    r1.modelo = "TAR_regime_1"
    r2.modelo = "TAR_regime_2"
    return ThresholdResult(
        threshold=float(threshold),
        n_regime_1=int(len(d1)),
        n_regime_2=int(len(d2)),
        resultado_regime_1=r1,
        resultado_regime_2=r2,
    )


def setar(y, lag=1, threshold=None) -> ThresholdResult:
    """
    Alias de TAR com mesmo mecanismo.
    """
    return tar(y=y, lag=lag, threshold=threshold)


def star(y, lag=1, gamma_grid=None, c_grid=None):
    """
    STAR logistico basico:
    y_t = a + b y_{t-1} + (a2 + b2 y_{t-1}) * G(z_t; gamma, c) + e_t
    G = 1 / (1 + exp(-gamma * (z_t - c))), z_t = y_{t-lag}
    """
    y_s = pd.Series(y).astype(float).rename("y")
    df = pd.DataFrame({"y": y_s, "ylag": y_s.shift(1), "gate": y_s.shift(lag)}).dropna()
    if len(df) < 30:
        raise ValueError("amostra insuficiente para STAR")

    if gamma_grid is None:
        gamma_grid = [1, 2, 5, 10, 20]
    if c_grid is None:
        qs = np.linspace(0.2, 0.8, 7)
        c_grid = [float(df["gate"].quantile(q)) for q in qs]

    best = None
    best_sse = np.inf
    for gamma in gamma_grid:
        for c in c_grid:
            G = 1.0 / (1.0 + np.exp(-gamma * (df["gate"] - c)))
            X = pd.DataFrame(
                {
                    "ylag": df["ylag"],
                    "G": G,
                    "G_ylag": G * df["ylag"],
                },
                index=df.index,
            )
            res = ols(df["y"], X, add_const=True)
            sse = float((res.resid**2).sum())
            if sse < best_sse:
                best_sse = sse
                best = (res, gamma, c)

    out, gamma_best, c_best = best
    out.modelo = "STAR(logistico)"
    out.extras["gamma"] = float(gamma_best)
    out.extras["c"] = float(c_best)
    out.extras["sse"] = float(best_sse)
    return out

