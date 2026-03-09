"""
data_economist.modelos — Modelos de séries temporais univariadas.

API pública
-----------
Família ARIMA
    ar(serie, lags, ...)
    ma(serie, lags, ...)
    arma(serie, p, q, ...)
    arima(serie, p, d, q, ...)
    sarima(serie, p, d, q, P, D, Q, s, ...)
    armax(serie, p, d, q, exog, ...)
    prever(resultado, steps, ...)

Seleção e diagnóstico
    auto_arima(serie, ...)
    criterios(serie, ordens, ...)
    acf_pacf(serie, ...)

Raiz unitária
    adf(serie, ...)
    pp(serie, ...)
    kpss(serie, ...)
    za(serie, ...)

Memória longa
    arfima(serie, p, q, ...)
    gph(serie, ...)

Dataclasses de resultado
    ModeloResult
    PrevisaoResult
    RaizResult
    ACFResult
"""

from .arima import ar, ma, arma, arima, sarima, armax, prever
from .selecao import auto_arima, criterios, acf_pacf
from .raiz_unitaria import adf, pp, kpss, za
from .arfima import arfima, gph
from ._resultado import ModeloResult, PrevisaoResult, RaizResult, ACFResult

__all__ = [
    # ARIMA
    "ar", "ma", "arma", "arima", "sarima", "armax", "prever",
    # Seleção
    "auto_arima", "criterios", "acf_pacf",
    # Raiz unitária
    "adf", "pp", "kpss", "za",
    # Memória longa
    "arfima", "gph",
    # Resultados
    "ModeloResult", "PrevisaoResult", "RaizResult", "ACFResult",
]
