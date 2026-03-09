"""
modelos/raiz_unitaria.py — Testes de raiz unitária e estacionariedade.

Funções
-------
adf(serie, ...)    Augmented Dickey-Fuller
pp(serie, ...)     Phillips-Perron
kpss(serie, ...)   KPSS (Kwiatkowski-Phillips-Schmidt-Shin)
za(serie, ...)     Zivot-Andrews (raiz unitária com quebra estrutural)
"""

from __future__ import annotations

import warnings
from typing import Optional

import pandas as pd

from ._resultado import RaizResult, _concluir_raiz


# ---------------------------------------------------------------------------
# ADF — Augmented Dickey-Fuller
# ---------------------------------------------------------------------------

def adf(
    serie: pd.Series,
    *,
    lags: Optional[int] = None,
    trend: str = "ct",
    autolag: str = "AIC",
    alpha: float = 0.05,
) -> RaizResult:
    """
    Teste Augmented Dickey-Fuller.

    H0: a série tem raiz unitária (não estacionária).

    Parâmetros
    ----------
    serie   : pd.Series
    lags    : int | None — se None, seleção automática por autolag
    trend   : 'n' sem drift | 'c' com drift | 'ct' drift + tendência | 'ctt'
    autolag : 'AIC' | 'BIC' | 't-stat'
    alpha   : nível de significância (padrão 0.05)

    Retorna RaizResult (rejeita_h0=True → série estacionária)
    """
    from statsmodels.tsa.stattools import adfuller

    s = serie.dropna()
    kwargs = {"regression": trend, "autolag": autolag if lags is None else None}
    if lags is not None:
        kwargs["maxlag"] = lags

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = adfuller(s, **kwargs)

    stat, pval, lags_used, nobs, criticos, *_ = res
    h0 = "serie tem raiz unitaria (nao estacionaria)"
    conclusao, rejeita = _concluir_raiz(pval, "ADF", h0, alpha)

    return RaizResult(
        statistic=float(stat),
        pvalue=float(pval),
        lags=int(lags_used),
        metodo="ADF",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        criticos={k: float(v) for k, v in criticos.items()},
    )


# ---------------------------------------------------------------------------
# PP — Phillips-Perron
# ---------------------------------------------------------------------------

def pp(
    serie: pd.Series,
    *,
    lags: Optional[int] = None,
    trend: str = "ct",
    alpha: float = 0.05,
) -> RaizResult:
    """
    Teste Phillips-Perron.

    H0: a série tem raiz unitária (não estacionária).
    Corrige a estatística ADF por heteroscedasticidade e autocorrelação (HAC/Newey-West).

    Parâmetros
    ----------
    serie : pd.Series
    lags  : int | None — número de lags HAC; None = regra de Newey-West (T^0.25)
    trend : 'n' | 'c' | 'ct'
    alpha : nível de significância

    Retorna RaizResult
    """
    import numpy as np
    import scipy.stats as sp
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tsa.tsatools import add_trend

    s = serie.dropna().values.astype(float)
    T = len(s)
    l = lags if lags is not None else int(4 * (T / 100) ** 0.25)

    # Regressão de Dickey-Fuller sem defasagens adicionais
    dy   = np.diff(s)
    y_lag = s[:-1]
    X = y_lag.reshape(-1, 1)
    if trend in ("c", "ct", "ctt"):
        X = np.column_stack([np.ones(len(dy)), X])
    if trend in ("ct", "ctt"):
        X = np.column_stack([X, np.arange(1, len(dy) + 1)])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res_ols = OLS(dy, X).fit()

    e = res_ols.resid
    n = len(e)

    # Estimativa HAC da variância de longo prazo (kernel de Bartlett)
    gamma0 = float(np.dot(e, e) / n)
    s2_lr  = gamma0
    for j in range(1, l + 1):
        w_j    = 1.0 - j / (l + 1)
        gamma_j = float(np.dot(e[j:], e[:-j]) / n)
        s2_lr  += 2 * w_j * gamma_j

    # Variância OLS do coeficiente de y_{t-1}
    idx_lag = 1 if trend in ("c", "ct", "ctt") else 0
    se2_ols = float(res_ols.bse[idx_lag] ** 2)
    coef    = float(res_ols.params[idx_lag])

    # Estatística PP corrigida
    t_ols   = float(res_ols.tvalues[idx_lag])
    xu      = X[:, idx_lag]
    xx_inv  = float(1.0 / np.dot(xu, xu))
    t_pp    = t_ols * np.sqrt(gamma0 / s2_lr) - 0.5 * (s2_lr - gamma0) * np.sqrt(xx_inv / s2_lr) * np.sqrt(n)

    # Valores críticos de MacKinnon (1994) para tau com trend
    _cv = {
        "n":  {1: -2.5658, 5: -1.9393, 10: -1.6156},
        "c":  {1: -3.4336, 5: -2.8621, 10: -2.5671},
        "ct": {1: -3.9638, 5: -3.4126, 10: -3.1279},
    }
    cv = _cv.get(trend, _cv["ct"])
    # p-valor aproximado por interpolação linear nos valores críticos
    cvs = [cv[1], cv[5], cv[10]]
    alphas_cv = [0.01, 0.05, 0.10]
    if t_pp < cvs[0]:
        pval = 0.005
    elif t_pp > cvs[2]:
        pval = 0.15
    else:
        # Interpolação linear
        for i in range(len(cvs) - 1):
            if cvs[i] <= t_pp <= cvs[i + 1]:
                frac = (t_pp - cvs[i]) / (cvs[i + 1] - cvs[i])
                pval = alphas_cv[i] + frac * (alphas_cv[i + 1] - alphas_cv[i])
                break
        else:
            pval = 0.10

    lags_val = l
    criticos = {"1%": cv[1], "5%": cv[5], "10%": cv[10]}
    h0 = "serie tem raiz unitaria (nao estacionaria)"
    conclusao, rejeita = _concluir_raiz(pval, "PP", h0, alpha)

    return RaizResult(
        statistic=float(t_pp),
        pvalue=float(pval),
        lags=lags_val,
        metodo="PP",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        criticos=criticos,
    )


# ---------------------------------------------------------------------------
# KPSS — Kwiatkowski-Phillips-Schmidt-Shin
# ---------------------------------------------------------------------------

def kpss(
    serie: pd.Series,
    *,
    trend: str = "c",
    lags: Optional[int] = None,
    alpha: float = 0.05,
) -> RaizResult:
    """
    Teste KPSS.

    H0: a série **é estacionária** (H0 inversa ao ADF).

    Parâmetros
    ----------
    serie : pd.Series
    trend : 'c' estacionária em nível | 'ct' estacionária em torno de tendência
    lags  : int | None — se None, usa regra de Schwert
    alpha : nível de significância

    Retorna RaizResult (rejeita_h0=True → série não estacionária)
    """
    from statsmodels.tsa.stattools import kpss as _kpss

    s = serie.dropna()
    nlags_val = lags if lags is not None else "auto"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, pval, lags_used, criticos = _kpss(s, regression=trend, nlags=nlags_val)

    h0 = "serie e estacionaria"
    conclusao, rejeita = _concluir_raiz(pval, "KPSS", h0, alpha)

    return RaizResult(
        statistic=float(stat),
        pvalue=float(pval),
        lags=int(lags_used),
        metodo="KPSS",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        criticos={k: float(v) for k, v in criticos.items()},
    )


# ---------------------------------------------------------------------------
# ZA — Zivot-Andrews
# ---------------------------------------------------------------------------

def za(
    serie: pd.Series,
    *,
    trend: str = "c",
    alpha: float = 0.05,
) -> RaizResult:
    """
    Teste Zivot-Andrews — raiz unitária com possível quebra estrutural endógena.

    H0: a série tem raiz unitária (sem quebra estrutural).

    Parâmetros
    ----------
    serie : pd.Series
    trend : 'c' quebra no intercepto | 't' quebra na tendência | 'ct' ambos
    alpha : nível de significância

    Retorna RaizResult com `criticos` incluindo o ponto de quebra estimado
    """
    from statsmodels.tsa.stattools import zivot_andrews

    s = serie.dropna()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, pval, criticos_dict, baselag, quebra = zivot_andrews(s, regression=trend)

    h0 = "serie tem raiz unitaria (sem quebra estrutural)"
    conclusao, rejeita = _concluir_raiz(pval, "Zivot-Andrews", h0, alpha)

    criticos_out = {}
    if isinstance(criticos_dict, dict):
        criticos_out = {k: float(v) for k, v in criticos_dict.items()}
    criticos_out["quebra_obs"] = int(quebra)

    return RaizResult(
        statistic=float(stat),
        pvalue=float(pval),
        lags=int(baselag),
        metodo="Zivot-Andrews",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        criticos=criticos_out,
    )
