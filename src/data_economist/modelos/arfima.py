"""
modelos/arfima.py — ARFIMA e estimação GPH para memória longa.

Funções
-------
arfima(serie, p, q, ...)    ARFIMA(p,d,q) com integração fracionária
gph(serie, ...)             Estimador log-periódico Geweke-Porter-Hudak
"""

from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd
import scipy.stats as sp

from ._resultado import ModeloResult


def _validar(serie: pd.Series) -> pd.Series:
    if not isinstance(serie, pd.Series):
        raise TypeError("serie deve ser pd.Series")
    s = serie.dropna()
    if len(s) < 20:
        raise ValueError("serie muito curta para ARFIMA (minimo 20 obs)")
    return s


# ---------------------------------------------------------------------------
# GPH — Geweke-Porter-Hudak
# ---------------------------------------------------------------------------

def gph(
    serie: pd.Series,
    *,
    bandwidth: Optional[int] = None,
) -> dict:
    """
    Estima o parâmetro de memória longa d via Geweke-Porter-Hudak (1983).

    O método regride o log do periodograma nas baixas frequências sobre
    log(4 * sin²(λ/2)), obtendo d como o negativo do coeficiente angular.

    Parâmetros
    ----------
    serie     : pd.Series — série temporal estacionária (ou diferenciada)
    bandwidth : int | None — número de frequências usadas (padrão: T^0.5 arredondado)

    Retorna dict com chaves:
        d        : estimativa pontual de d
        se       : erro padrão de d
        pvalue   : p-valor para H0: d=0
        ic_95    : intervalo de confiança 95% para d
        bandwidth: m usado
    """
    s = _validar(serie)
    T = len(s)
    m = bandwidth if bandwidth is not None else max(2, int(np.round(T ** 0.5)))
    m = min(m, T // 2 - 1)

    # Periodograma (estimador do espectro)
    fft_vals = np.fft.rfft(s.values - s.values.mean())
    periodo  = (np.abs(fft_vals) ** 2) / (2 * np.pi * T)

    # Frequências 1..m
    freqs = np.arange(1, m + 1) * 2 * np.pi / T
    x = np.log(4 * np.sin(freqs / 2) ** 2)
    y = np.log(periodo[1 : m + 1])

    # Regressão OLS: y = c + beta * x + eps  →  d_hat = -beta
    xm = x - x.mean()
    beta = float(np.dot(xm, y) / np.dot(xm, xm))
    d_hat = -beta

    # Variância (assintótica: pi²/6 / sum(xm²))
    residuos = y - (y.mean() + beta * xm)
    s2 = float(np.dot(residuos, residuos) / (m - 2)) if m > 2 else float("nan")
    var_beta = s2 / float(np.dot(xm, xm))
    se = float(np.sqrt(var_beta)) if var_beta > 0 else float("nan")

    tstat = d_hat / se if se > 0 else float("nan")
    pval  = float(2 * sp.t.sf(abs(tstat), df=m - 2)) if not np.isnan(tstat) else float("nan")
    ic    = (d_hat - 1.96 * se, d_hat + 1.96 * se)

    return {
        "d":         float(d_hat),
        "se":        se,
        "pvalue":    pval,
        "ic_95":     ic,
        "bandwidth": m,
    }


# ---------------------------------------------------------------------------
# Diferenciação fracionária (filtro binomial)
# ---------------------------------------------------------------------------

def _diferenciar_fracionario(serie: np.ndarray, d: float, max_lags: int = 300) -> np.ndarray:
    """
    Aplica diferenciação fracionária usando expansão binomial truncada.

    (1 - L)^d x_t = sum_{k=0}^{K} binom(d, k) * (-1)^k * x_{t-k}
    """
    T = len(serie)
    # Evita perder quase toda a amostra quando T é pequeno.
    # Para estabilidade prática, limitamos K a no máximo metade da amostra.
    K = min(max_lags, max(1, T // 2))

    # Coeficientes binomiais generalizados
    weights = np.ones(K + 1)
    for k in range(1, K + 1):
        weights[k] = weights[k - 1] * (d - k + 1) / k * (-1)

    result = np.full(T, np.nan)
    for t in range(K, T):
        # t - K - 1 pode ser -1, que Python interpreta como índice final.
        # Usamos None para evitar ambiguidade no slice.
        stop = t - K - 1
        chunk = serie[t:stop if stop >= 0 else None:-1]
        result[t] = float(np.dot(weights[:len(chunk)], chunk))

    return result


# ---------------------------------------------------------------------------
# ARFIMA(p, d, q)
# ---------------------------------------------------------------------------

def arfima(
    serie: pd.Series,
    p: int,
    q: int,
    *,
    d: Optional[float] = None,
    trend: str = "n",
    max_lags: int = 300,
) -> ModeloResult:
    """
    Estima ARFIMA(p,d,q) com integração fracionária.

    Abordagem em dois passos:
    1. Se d não fornecido, estima d via GPH.
    2. Aplica diferenciação fracionária (filtro binomial) com o d estimado.
    3. Estima ARMA(p,q) sobre a série filtrada via statsmodels.

    Parâmetros
    ----------
    serie    : pd.Series com índice datetime
    p        : ordem AR
    q        : ordem MA
    d        : float | None — parâmetro fracionário; se None, estimado via GPH
    trend    : 'n' | 'c' | 'ct'
    max_lags : truncamento do filtro binomial (padrão 300)

    Retorna ModeloResult com campo extra `params["d_fracionario"]`
    """
    from statsmodels.tsa.arima.model import ARIMA as _ARIMA

    s = _validar(serie)

    # Passo 1: estimar d se não fornecido
    if d is None:
        gph_res = gph(s)
        d_est   = float(gph_res["d"])
    else:
        d_est = float(d)

    # Passo 2: diferenciar fracionariamente
    s_arr    = s.values.astype(float)
    s_filt   = _diferenciar_fracionario(s_arr, d_est, max_lags=max_lags)

    # Remover NaN iniciais (período de warmup do filtro)
    valid    = ~np.isnan(s_filt)
    idx_val  = s.index[valid]
    s_filt_s = pd.Series(s_filt[valid], index=idx_val, name=s.name)

    # Fallback: se ainda ficou muito curta para ARMA(p,q), reduz truncamento.
    min_obs = max(12, p + q + 8)
    if len(s_filt_s) < min_obs:
        s_filt = _diferenciar_fracionario(s_arr, d_est, max_lags=max(5, len(s_arr) // 4))
        valid = ~np.isnan(s_filt)
        idx_val = s.index[valid]
        s_filt_s = pd.Series(s_filt[valid], index=idx_val, name=s.name)

    # Passo 3: estimar ARMA sobre a série filtrada
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if p + q == 0:
            # Apenas o filtro fracionário — modelo trivial
            from statsmodels.tsa.arima.model import ARIMA as _AR0
            fit = _AR0(s_filt_s, order=(0, 0, 0), trend=trend).fit()
        else:
            fit = _ARIMA(s_filt_s, order=(p, 0, q), trend=trend).fit()

    # Extrair resultado base
    try:
        params_fit  = fit.params
        pvalues_fit = fit.pvalues
    except AttributeError:
        params_fit  = pd.Series(dtype=float)
        pvalues_fit = pd.Series(dtype=float)

    # Acrescentar d fracionário aos parâmetros
    params_out  = pd.concat([pd.Series({"d_fracionario": d_est}), params_fit])
    pvalues_out = pd.concat([pd.Series({"d_fracionario": float("nan")}), pvalues_fit])

    residuos = pd.Series(fit.resid, index=s_filt_s.index[-len(fit.resid):], name="residuo")
    fitted   = pd.Series(fit.fittedvalues, index=s_filt_s.index[-len(fit.fittedvalues):], name="fitted")

    try:
        hqic = float(fit.hqic)
    except AttributeError:
        k = len(params_fit)
        n = fit.nobs
        import numpy as _np
        hqic = -2 * fit.llf + 2 * k * _np.log(_np.log(n)) if n > 1 else float("nan")

    return ModeloResult(
        modelo=f"ARFIMA({p},{d_est:.4f},{q})",
        params=params_out,
        pvalues=pvalues_out,
        aic=float(fit.aic),
        bic=float(fit.bic),
        hqic=hqic,
        log_likelihood=float(fit.llf),
        residuos=residuos,
        fitted=fitted,
        nobs=int(fit.nobs),
        ordem=(p, d_est, q),
        _fit=fit,
    )
