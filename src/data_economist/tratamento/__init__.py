"""
Módulo tratamento: ferramentas de análise e tratamento de séries temporais.

Funcionalidades
---------------
Filtros de ciclo e tendência:
    hp(serie, lamb=None)              Filtro Hodrick-Prescott
    bk(serie, low, high, K)           Filtro Baxter-King (passa-banda, comprimento fixo)
    cf(serie, low, high, drift, ...)  Filtro Christiano-Fitzgerald (passa-banda)
    tendencia(resultado)              Extrai componente tendência de FilterResult
    ciclo(resultado)                  Extrai componente cíclico de FilterResult

Suavização exponencial:
    ses(serie, alpha)                 Suavização Exponencial Simples
    des(serie, alpha, beta)           Suavização Exponencial Dupla
    holt(serie, alpha, beta, damped)  Método de Holt (tendência linear)
    holt_winters(serie, seasonal, m)  Método de Holt-Winters (tendência + sazonalidade)
    ets(serie, auto, ...)             ETS com seleção automática por AIC
    suavizado(resultado)              Extrai série suavizada in-sample de SmoothResult
    forecast(resultado, steps)        Gera previsão fora da amostra

Conversão de frequência:
    para_frequencia(serie, freq, metodo)
        Alta para baixa: mean, sum, first, last, max, min
        Baixa para alta: linear, quadratic, cubic, ffill, pchip, spline

Pré-branqueamento:
    whitening(serie, lags, criterio)  Ajuste AR(p) e extração dos resíduos
    serie_branca(resultado)           Extrai resíduos de WhiteResult

Entrada esperada
----------------
Todas as funções aceitam pd.Series com DatetimeIndex e frequência regular.
"""

from .filtros import (
    FilterResult,
    bk,
    cf,
    ciclo,
    hp,
    tendencia,
)
from .frequencia import para_frequencia
from .suavizacao import (
    SmoothResult,
    des,
    ets,
    forecast,
    holt,
    holt_winters,
    ses,
    suavizado,
)
from .whitening import (
    WhiteResult,
    serie_branca,
    whitening,
)

__all__ = [
    # filtros
    "FilterResult",
    "hp",
    "bk",
    "cf",
    "tendencia",
    "ciclo",
    # suavização
    "SmoothResult",
    "ses",
    "des",
    "holt",
    "holt_winters",
    "ets",
    "suavizado",
    "forecast",
    # frequência
    "para_frequencia",
    # whitening
    "WhiteResult",
    "whitening",
    "serie_branca",
]
