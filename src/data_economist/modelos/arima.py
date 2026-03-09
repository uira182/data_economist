"""
modelos/arima.py — Família ARMA / ARIMA / SARIMA / ARMAX.

Funções
-------
ar(serie, lags, ...)            AR(p)
ma(serie, lags, ...)            MA(q)
arma(serie, p, q, ...)          ARMA(p,q)
arima(serie, p, d, q, ...)      ARIMA(p,d,q)
sarima(serie, p,d,q,P,D,Q,s)    SARIMA(p,d,q)(P,D,Q)[s]
armax(serie, p, d, q, exog)     ARMAX com variáveis exógenas
prever(resultado, steps, ...)   Previsão fora da amostra

Todos retornam ModeloResult (exceto prever, que retorna PrevisaoResult).
"""

from __future__ import annotations

import warnings
from typing import Optional, Union

import numpy as np
import pandas as pd

from ._resultado import ModeloResult, PrevisaoResult


def _validar(serie: pd.Series) -> pd.Series:
    if not isinstance(serie, pd.Series):
        raise TypeError("serie deve ser pd.Series")
    if len(serie) < 10:
        raise ValueError("serie muito curta (minimo 10 obs)")
    s = serie.dropna()
    if len(s) < 10:
        raise ValueError("serie tem menos de 10 valores validos apos dropna")
    return s


def _inferir_freq(serie: pd.Series) -> Optional[str]:
    if hasattr(serie.index, "freq") and serie.index.freq is not None:
        return series_freq_str(serie)
    try:
        inferred = pd.infer_freq(serie.index)
        return inferred
    except Exception:
        return None


def series_freq_str(serie: pd.Series) -> Optional[str]:
    try:
        return pd.tseries.frequencies.to_offset(serie.index.freq).freqstr
    except Exception:
        return None


def _extrair_resultado(fit, nome: str, ordem: tuple, serie: pd.Series) -> ModeloResult:
    residuos = pd.Series(fit.resid, index=serie.index[-len(fit.resid):], name="residuo")
    fitted   = pd.Series(fit.fittedvalues, index=serie.index[-len(fit.fittedvalues):], name="fitted")

    try:
        params  = fit.params
        pvalues = fit.pvalues
    except AttributeError:
        params  = pd.Series(dtype=float)
        pvalues = pd.Series(dtype=float)

    try:
        hqic = float(fit.hqic)
    except AttributeError:
        k = len(params)
        n = fit.nobs
        hqic = -2 * fit.llf + 2 * k * np.log(np.log(n)) if n > 1 else float("nan")

    return ModeloResult(
        modelo=nome,
        params=params,
        pvalues=pvalues,
        aic=float(fit.aic),
        bic=float(fit.bic),
        hqic=hqic,
        log_likelihood=float(fit.llf),
        residuos=residuos,
        fitted=fitted,
        nobs=int(fit.nobs),
        ordem=ordem,
        _fit=fit,
    )


# ---------------------------------------------------------------------------
# AR(p)
# ---------------------------------------------------------------------------

def ar(
    serie: pd.Series,
    lags: int,
    *,
    trend: str = "c",
    method: str = "cmle",
) -> ModeloResult:
    """
    Estima AR(p).

    Parâmetros
    ----------
    serie  : pd.Series com índice datetime
    lags   : int — ordem p
    trend  : 'n' sem constante | 'c' com constante | 'ct' constante + tendência
    method : 'cmle' | 'mle' | 'yw'

    Retorna ModeloResult
    """
    from statsmodels.tsa.ar_model import AutoReg

    s = _validar(serie)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = AutoReg(s, lags=lags, trend=trend).fit()

    return _extrair_resultado(fit, f"AR({lags})", (lags, 0, 0), s)


# ---------------------------------------------------------------------------
# MA(q)
# ---------------------------------------------------------------------------

def ma(
    serie: pd.Series,
    lags: int,
    *,
    trend: str = "c",
) -> ModeloResult:
    """
    Estima MA(q).

    Parâmetros
    ----------
    serie : pd.Series com índice datetime
    lags  : int — ordem q
    trend : 'n' | 'c' | 'ct'

    Retorna ModeloResult
    """
    from statsmodels.tsa.arima.model import ARIMA as _ARIMA

    s = _validar(serie)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = _ARIMA(s, order=(0, 0, lags), trend=trend).fit()

    return _extrair_resultado(fit, f"MA({lags})", (0, 0, lags), s)


# ---------------------------------------------------------------------------
# ARMA(p, q)
# ---------------------------------------------------------------------------

def arma(
    serie: pd.Series,
    p: int,
    q: int,
    *,
    trend: str = "c",
) -> ModeloResult:
    """
    Estima ARMA(p,q).

    Parâmetros
    ----------
    serie : pd.Series com índice datetime
    p     : ordem AR
    q     : ordem MA
    trend : 'n' | 'c' | 'ct'

    Retorna ModeloResult
    """
    from statsmodels.tsa.arima.model import ARIMA as _ARIMA

    s = _validar(serie)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = _ARIMA(s, order=(p, 0, q), trend=trend).fit()

    return _extrair_resultado(fit, f"ARMA({p},{q})", (p, 0, q), s)


# ---------------------------------------------------------------------------
# ARIMA(p, d, q)
# ---------------------------------------------------------------------------

def arima(
    serie: pd.Series,
    p: int,
    d: int,
    q: int,
    *,
    trend: str = "n",
    method: str = "innovations_mle",
) -> ModeloResult:
    """
    Estima ARIMA(p,d,q).

    Parâmetros
    ----------
    serie  : pd.Series com índice datetime
    p      : ordem AR
    d      : grau de integração (nº de diferenças)
    q      : ordem MA
    trend  : 'n' | 'c' | 'ct'
    method : 'innovations_mle' | 'statespace' | 'hannan_rissanen' | 'burg'

    Retorna ModeloResult
    """
    from statsmodels.tsa.arima.model import ARIMA as _ARIMA

    s = _validar(serie)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = _ARIMA(s, order=(p, d, q), trend=trend).fit(method=method)

    return _extrair_resultado(fit, f"ARIMA({p},{d},{q})", (p, d, q), s)


# ---------------------------------------------------------------------------
# SARIMA(p,d,q)(P,D,Q)[s]
# ---------------------------------------------------------------------------

def sarima(
    serie: pd.Series,
    p: int,
    d: int,
    q: int,
    P: int,
    D: int,
    Q: int,
    s: int,
    *,
    trend: str = "n",
) -> ModeloResult:
    """
    Estima SARIMA(p,d,q)(P,D,Q)[s].

    Parâmetros
    ----------
    serie : pd.Series com índice datetime
    p,d,q : parte não-sazonal
    P,D,Q : parte sazonal
    s     : periodicidade (12=mensal, 4=trimestral, 7=diário)
    trend : 'n' | 'c' | 'ct'

    Retorna ModeloResult
    """
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    s_val = s
    serie_s = _validar(serie)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SARIMAX(
            serie_s,
            order=(p, d, q),
            seasonal_order=(P, D, Q, s_val),
            trend=trend,
        ).fit(disp=False)

    nome  = f"SARIMA({p},{d},{q})({P},{D},{Q})[{s_val}]"
    ordem = (p, d, q, P, D, Q, s_val)
    return _extrair_resultado(fit, nome, ordem, serie_s)


# ---------------------------------------------------------------------------
# ARMAX
# ---------------------------------------------------------------------------

def armax(
    serie: pd.Series,
    p: int,
    d: int,
    q: int,
    exog: Union[pd.DataFrame, np.ndarray],
    *,
    trend: str = "n",
) -> ModeloResult:
    """
    Estima ARMAX — ARIMA(p,d,q) com variáveis exógenas.

    Parâmetros
    ----------
    serie : pd.Series com índice datetime
    p,d,q : ordem ARIMA
    exog  : pd.DataFrame ou np.ndarray — variáveis exógenas (mesma dimensão da serie)
    trend : 'n' | 'c' | 'ct'

    Retorna ModeloResult
    """
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    s = _validar(serie)
    if isinstance(exog, pd.DataFrame):
        exog_val = exog.loc[s.index] if hasattr(exog, "loc") else exog
    else:
        exog_val = exog

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SARIMAX(
            s,
            exog=exog_val,
            order=(p, d, q),
            trend=trend,
        ).fit(disp=False)

    return _extrair_resultado(fit, f"ARMAX({p},{d},{q})+exog", (p, d, q), s)


# ---------------------------------------------------------------------------
# Previsão fora da amostra
# ---------------------------------------------------------------------------

def prever(
    resultado: ModeloResult,
    steps: int,
    *,
    alpha: float = 0.05,
    exog: Optional[Union[pd.DataFrame, np.ndarray]] = None,
) -> PrevisaoResult:
    """
    Gera previsão fora da amostra a partir de um ModeloResult.

    Parâmetros
    ----------
    resultado : ModeloResult retornado por ar(), arima(), sarima(), etc.
    steps     : int — número de períodos à frente
    alpha     : float — nível do intervalo de confiança (padrão 0.05 → IC 95%)
    exog      : variáveis exógenas futuras (apenas para ARMAX)

    Retorna PrevisaoResult
    """
    if resultado._fit is None:
        raise ValueError("ModeloResult nao contem objeto fit interno")

    fit = resultado._fit

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kwargs = {"steps": steps, "alpha": alpha}
        if exog is not None:
            kwargs["exog"] = exog

        try:
            forecast = fit.get_forecast(**kwargs)
            summary  = forecast.summary_frame(alpha=alpha)
            valores  = summary["mean"]
            ic_lower = summary["mean_ci_lower"]
            ic_upper = summary["mean_ci_upper"]
        except (AttributeError, TypeError):
            # AutoReg usa interface diferente
            pred     = fit.forecast(steps=steps)
            valores  = pred
            ic_lower = pred * np.nan
            ic_upper = pred * np.nan

    # Inferir índice de datas futuras
    last_date = resultado.fitted.index[-1]
    try:
        freq = pd.infer_freq(resultado.fitted.index)
        if freq is None:
            freq = pd.tseries.frequencies.to_offset(
                resultado.fitted.index.freq
            ).freqstr
        idx_fut = pd.date_range(start=last_date, periods=steps + 1, freq=freq)[1:]
    except Exception:
        idx_fut = pd.RangeIndex(steps)

    valores.index  = idx_fut
    ic_lower.index = idx_fut
    ic_upper.index = idx_fut

    return PrevisaoResult(
        valores=valores.rename("previsao"),
        ic_lower=ic_lower.rename("ic_lower"),
        ic_upper=ic_upper.rename("ic_upper"),
        steps=steps,
        alpha=alpha,
    )
