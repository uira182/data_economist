"""
Suavização exponencial de séries temporais.

Implementa:
- SES  — Suavização Exponencial Simples
- DES  — Suavização Exponencial Dupla
- Holt — Tendência linear (com ou sem amortecimento)
- Holt-Winters — Sazonalidade aditiva ou multiplicativa
- ETS  — Error/Trend/Seasonal com seleção automática por AIC

Entrada esperada: pd.Series com DatetimeIndex e frequência regular.
"""

from __future__ import annotations

import itertools
import warnings
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd

# períodos sazonais padrão por frequência
_SEASONAL_PERIODS: dict[str, int] = {
    "M": 12,
    "Q": 4,
    "W": 52,
    "D": 7,
    "A": 1,
    "Y": 1,
}


def _infer_seasonal_periods(series: pd.Series) -> int:
    """Infere o número de períodos sazonais pela frequência do índice."""
    freq_str = getattr(series.index, "freqstr", None)
    if freq_str is None:
        return 12
    freq_str = freq_str.upper().split("-")[0]  # "QE-DEC" → "QE"
    for key, m in _SEASONAL_PERIODS.items():
        if freq_str.startswith(key):
            return m
    return 12


def _validate_series(series: pd.Series, nome_funcao: str) -> None:
    """Valida que a série tem DatetimeIndex e tamanho mínimo."""
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError(
            f"{nome_funcao}(): a série deve ter DatetimeIndex. "
            f"Tipo atual: {type(series.index).__name__}"
        )
    if len(series.dropna()) < 3:
        raise ValueError(
            f"{nome_funcao}(): a série precisa de ao menos 3 observações."
        )


@dataclass
class SmoothResult:
    """
    Resultado de um método de suavização exponencial.

    Atributos
    ---------
    original : pd.Series
        Série original fornecida.
    suavizado : pd.Series
        Valores ajustados in-sample (fitted values).
    alpha : float ou None
        Parâmetro de suavização do nível.
    beta : float ou None
        Parâmetro de suavização da tendência (Holt e Holt-Winters).
    gamma : float ou None
        Parâmetro de suavização sazonal (Holt-Winters e ETS com sazonalidade).
    aic : float ou None
        Critério de informação de Akaike do modelo ajustado.
    metodo : str
        Nome do método: "ses", "des", "holt", "holt_winters" ou "ets".
    params : dict
        Parâmetros efetivamente usados.
    _model_fit : objeto statsmodels
        Referência interna ao modelo ajustado, usada por forecast().
    """

    original: pd.Series
    suavizado: pd.Series
    alpha: Optional[float]
    beta: Optional[float]
    gamma: Optional[float]
    aic: Optional[float]
    metodo: str
    params: dict = field(default_factory=dict)
    _model_fit: Any = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# Suavização Exponencial Simples (SES)
# ---------------------------------------------------------------------------

def ses(series: pd.Series, alpha: Optional[float] = None) -> SmoothResult:
    """
    Suavização Exponencial Simples.

    Fórmula: S_t = alpha * y_t + (1 - alpha) * S_{t-1}

    Adequada para séries sem tendência e sem sazonalidade.

    Parâmetros
    ----------
    series : pd.Series
        Série temporal com DatetimeIndex.
    alpha : float, opcional
        Parâmetro de suavização (0 < alpha < 1).
        Se None, é estimado por máxima verossimilhança.

    Retorna
    -------
    SmoothResult
    """
    _validate_series(series, "ses")

    from statsmodels.tsa.holtwinters import SimpleExpSmoothing

    s = series.dropna()
    kwargs: dict[str, Any] = {"optimized": alpha is None}
    if alpha is not None:
        kwargs["smoothing_level"] = alpha
        kwargs["optimized"] = False

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SimpleExpSmoothing(s).fit(**kwargs)

    alpha_used = float(fit.params["smoothing_level"])
    fitted = pd.Series(fit.fittedvalues, index=s.index, name="suavizado")

    return SmoothResult(
        original=series,
        suavizado=fitted,
        alpha=alpha_used,
        beta=None,
        gamma=None,
        aic=float(fit.aic) if hasattr(fit, "aic") else None,
        metodo="ses",
        params={"alpha": alpha_used},
        _model_fit=fit,
    )


# ---------------------------------------------------------------------------
# Suavização Exponencial Dupla (DES)
# ---------------------------------------------------------------------------

def des(
    series: pd.Series,
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
) -> SmoothResult:
    """
    Suavização Exponencial Dupla.

    Aplica a suavização exponencial ao nível e à tendência com função
    de tendência exponencial (multiplicativa).
    Adequada para séries com tendência sem sazonalidade.

    Parâmetros
    ----------
    series : pd.Series
        Série temporal com DatetimeIndex.
    alpha : float, opcional
        Parâmetro de suavização do nível. Se None, estimado automaticamente.
    beta : float, opcional
        Parâmetro de suavização da tendência. Se None, estimado automaticamente.

    Retorna
    -------
    SmoothResult
    """
    _validate_series(series, "des")

    from statsmodels.tsa.holtwinters import Holt

    s = series.dropna()
    optimized = alpha is None and beta is None
    fit_kwargs: dict[str, Any] = {"optimized": optimized}
    if alpha is not None:
        fit_kwargs["smoothing_level"] = alpha
    if beta is not None:
        fit_kwargs["smoothing_trend"] = beta

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = Holt(s, exponential=True).fit(**fit_kwargs)

    alpha_used = float(fit.params["smoothing_level"])
    beta_used = float(fit.params["smoothing_trend"])
    fitted = pd.Series(fit.fittedvalues, index=s.index, name="suavizado")

    return SmoothResult(
        original=series,
        suavizado=fitted,
        alpha=alpha_used,
        beta=beta_used,
        gamma=None,
        aic=float(fit.aic) if hasattr(fit, "aic") else None,
        metodo="des",
        params={"alpha": alpha_used, "beta": beta_used, "exponential": True},
        _model_fit=fit,
    )


# ---------------------------------------------------------------------------
# Holt (tendência linear)
# ---------------------------------------------------------------------------

def holt(
    series: pd.Series,
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    damped: bool = False,
) -> SmoothResult:
    """
    Método de Holt (tendência linear, com ou sem amortecimento).

    Equações:
      Nível:    L_t = alpha * y_t + (1 - alpha) * (L_{t-1} + T_{t-1})
      Tendência: T_t = beta * (L_t - L_{t-1}) + (1 - beta) * T_{t-1}

    Com amortecimento (damped=True), a tendência é multiplicada por phi^h
    na previsão, onde 0 < phi < 1.

    Parâmetros
    ----------
    series : pd.Series
        Série temporal com DatetimeIndex.
    alpha : float, opcional
        Parâmetro de suavização do nível.
    beta : float, opcional
        Parâmetro de suavização da tendência.
    damped : bool
        Se True, usa tendência amortecida (padrão False).

    Retorna
    -------
    SmoothResult
    """
    _validate_series(series, "holt")

    from statsmodels.tsa.holtwinters import Holt

    s = series.dropna()
    optimized = alpha is None and beta is None
    fit_kwargs: dict[str, Any] = {"optimized": optimized}
    if alpha is not None:
        fit_kwargs["smoothing_level"] = alpha
    if beta is not None:
        fit_kwargs["smoothing_trend"] = beta

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = Holt(s, damped_trend=damped).fit(**fit_kwargs)

    alpha_used = float(fit.params["smoothing_level"])
    beta_used = float(fit.params["smoothing_trend"])
    fitted = pd.Series(fit.fittedvalues, index=s.index, name="suavizado")

    return SmoothResult(
        original=series,
        suavizado=fitted,
        alpha=alpha_used,
        beta=beta_used,
        gamma=None,
        aic=float(fit.aic) if hasattr(fit, "aic") else None,
        metodo="holt",
        params={"alpha": alpha_used, "beta": beta_used, "damped": damped},
        _model_fit=fit,
    )


# ---------------------------------------------------------------------------
# Holt-Winters
# ---------------------------------------------------------------------------

def holt_winters(
    series: pd.Series,
    seasonal: str = "add",
    m: Optional[int] = None,
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    gamma: Optional[float] = None,
    damped: bool = False,
) -> SmoothResult:
    """
    Método de Holt-Winters (tendência + sazonalidade).

    Aditivo: y_t = L_{t-1} + T_{t-1} + S_{t-m} + e_t
    Multiplicativo: y_t = (L_{t-1} + T_{t-1}) * S_{t-m} + e_t

    Parâmetros
    ----------
    series : pd.Series
        Série temporal com DatetimeIndex.
    seasonal : str
        "add" (sazonalidade aditiva) ou "mul" (multiplicativa).
    m : int, opcional
        Número de períodos sazonais. Inferido automaticamente pela frequência
        (12 para mensal, 4 para trimestral, etc.).
    alpha : float, opcional
        Parâmetro de nível. Se None, estimado automaticamente.
    beta : float, opcional
        Parâmetro de tendência.
    gamma : float, opcional
        Parâmetro sazonal.
    damped : bool
        Se True, usa tendência amortecida.

    Retorna
    -------
    SmoothResult
    """
    if seasonal not in ("add", "mul"):
        raise ValueError("holt_winters(): seasonal deve ser 'add' ou 'mul'.")

    _validate_series(series, "holt_winters")

    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    s = series.dropna()
    m_used = m if m is not None else _infer_seasonal_periods(series)

    if len(s) < 2 * m_used:
        raise ValueError(
            f"holt_winters(): a série precisa de pelo menos {2 * m_used} "
            f"observações para m={m_used}."
        )

    optimized = alpha is None and beta is None and gamma is None
    fit_kwargs: dict[str, Any] = {"optimized": optimized}
    if alpha is not None:
        fit_kwargs["smoothing_level"] = alpha
    if beta is not None:
        fit_kwargs["smoothing_trend"] = beta
    if gamma is not None:
        fit_kwargs["smoothing_seasonal"] = gamma

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ExponentialSmoothing(
            s,
            trend="add",
            seasonal=seasonal,
            seasonal_periods=m_used,
            damped_trend=damped,
        )
        fit = model.fit(**fit_kwargs)

    alpha_used = float(fit.params["smoothing_level"])
    beta_used = float(fit.params["smoothing_trend"])
    gamma_used = float(fit.params["smoothing_seasonal"])
    fitted = pd.Series(fit.fittedvalues, index=s.index, name="suavizado")

    return SmoothResult(
        original=series,
        suavizado=fitted,
        alpha=alpha_used,
        beta=beta_used,
        gamma=gamma_used,
        aic=float(fit.aic) if hasattr(fit, "aic") else None,
        metodo="holt_winters",
        params={
            "alpha": alpha_used,
            "beta": beta_used,
            "gamma": gamma_used,
            "seasonal": seasonal,
            "m": m_used,
            "damped": damped,
        },
        _model_fit=fit,
    )


# ---------------------------------------------------------------------------
# ETS (Error-Trend-Seasonal com seleção automática)
# ---------------------------------------------------------------------------

# combinações válidas para seleção automática
_ETS_ERRORS = ["add", "mul"]
_ETS_TRENDS = [None, "add"]
_ETS_SEASONALS = [None, "add", "mul"]


def ets(
    series: pd.Series,
    error: str = "add",
    trend: Optional[str] = None,
    seasonal: Optional[str] = None,
    m: Optional[int] = None,
    auto: bool = True,
    damped_trend: bool = False,
) -> SmoothResult:
    """
    Modelo ETS (Error-Trend-Seasonal) com seleção automática por AIC.

    Quando auto=True, itera sobre combinações de erro (A/M), tendência (N/A)
    e sazonalidade (N/A/M) e seleciona o modelo com menor AIC.
    Equivalente ao auto.ets() do R (pacote forecast).

    Parâmetros
    ----------
    series : pd.Series
        Série temporal com DatetimeIndex.
    error : str
        Componente de erro: "add" ou "mul" (usado quando auto=False).
    trend : str ou None
        Componente de tendência: None, "add" (usado quando auto=False).
    seasonal : str ou None
        Componente sazonal: None, "add" ou "mul" (usado quando auto=False).
    m : int, opcional
        Número de períodos sazonais. Inferido automaticamente se None.
    auto : bool
        Se True, seleciona automaticamente o melhor modelo por AIC (padrão True).
    damped_trend : bool
        Se True, usa tendência amortecida (usado quando auto=False).

    Retorna
    -------
    SmoothResult
        Inclui .aic com o critério do modelo selecionado.
    """
    _validate_series(series, "ets")

    from statsmodels.tsa.exponential_smoothing.ets import ETSModel

    s = series.dropna()
    m_used = m if m is not None else _infer_seasonal_periods(series)

    if not auto:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ETSModel(
                s,
                error=error,
                trend=trend,
                seasonal=seasonal,
                seasonal_periods=m_used if seasonal is not None else None,
                damped_trend=damped_trend,
            )
            fit = model.fit(disp=False)
        return _ets_result(series, s, fit, error, trend, seasonal, m_used, damped_trend)

    # Seleção automática por AIC
    best_fit = None
    best_aic = float("inf")
    best_combo: tuple = ("add", None, None, False)

    for err, trd, seas in itertools.product(_ETS_ERRORS, _ETS_TRENDS, _ETS_SEASONALS):
        for damp in ([False, True] if trd is not None else [False]):
            try:
                sp = m_used if seas is not None else None
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model = ETSModel(
                        s,
                        error=err,
                        trend=trd,
                        seasonal=seas,
                        seasonal_periods=sp,
                        damped_trend=damp,
                    )
                    fit = model.fit(disp=False)
                if fit.aic < best_aic:
                    best_aic = fit.aic
                    best_fit = fit
                    best_combo = (err, trd, seas, damp)
            except Exception:
                continue

    if best_fit is None:
        raise RuntimeError(
            "ets(): nenhum modelo ETS convergiu. Verifique a série de entrada."
        )

    err_b, trd_b, seas_b, damp_b = best_combo
    return _ets_result(series, s, best_fit, err_b, trd_b, seas_b, m_used, damp_b)


def _ets_result(
    original: pd.Series,
    s: pd.Series,
    fit: Any,
    error: str,
    trend: Optional[str],
    seasonal: Optional[str],
    m: int,
    damped: bool,
) -> SmoothResult:
    """Constrói o SmoothResult a partir de um modelo ETS ajustado."""
    fitted = pd.Series(fit.fittedvalues, index=s.index, name="suavizado")

    params = fit.params
    alpha = float(params.get("smoothing_level", params.get("alpha", float("nan"))))
    beta = float(params.get("smoothing_trend", params.get("beta", float("nan")))) if trend else None
    gamma = float(params.get("smoothing_seasonal", params.get("gamma", float("nan")))) if seasonal else None

    return SmoothResult(
        original=original,
        suavizado=fitted,
        alpha=alpha if not pd.isna(alpha) else None,
        beta=beta if beta is not None and not pd.isna(beta) else None,
        gamma=gamma if gamma is not None and not pd.isna(gamma) else None,
        aic=float(fit.aic),
        metodo="ets",
        params={
            "error": error,
            "trend": trend,
            "seasonal": seasonal,
            "m": m,
            "damped_trend": damped,
        },
        _model_fit=fit,
    )


# ---------------------------------------------------------------------------
# Funções extratoras
# ---------------------------------------------------------------------------

def suavizado(resultado: SmoothResult) -> pd.Series:
    """Devolve os valores suavizados in-sample."""
    return resultado.suavizado


def forecast(resultado: SmoothResult, steps: int = 12) -> pd.Series:
    """
    Gera previsão fora da amostra.

    Parâmetros
    ----------
    resultado : SmoothResult
        Resultado de ses(), des(), holt(), holt_winters() ou ets().
    steps : int
        Número de períodos à frente a prever (padrão 12).

    Retorna
    -------
    pd.Series
        Valores previstos com índice de datas gerado automaticamente.
    """
    if resultado._model_fit is None:
        raise RuntimeError("forecast(): modelo interno não disponível.")

    fit = resultado._model_fit
    pred = fit.forecast(steps)
    return pd.Series(pred.values, index=pred.index, name="forecast")
