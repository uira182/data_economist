"""
data_economist.regressao — Regressao e estimacao de equacao unica.
"""

from ._resultado import RegResult, NLSResult, StepwiseResult, ThresholdResult
from .linear import ols, wls, robusta, quantilica, vif, coeficientes_padronizados, elasticidades, elipse_confianca
from .nao_linear import nls
from .selecao import stepwise
from .dinamicos import pdl, ardl, ardl_bounds
from .limiar import tar, setar, star

__all__ = [
    "RegResult",
    "NLSResult",
    "StepwiseResult",
    "ThresholdResult",
    "ols",
    "wls",
    "robusta",
    "quantilica",
    "vif",
    "coeficientes_padronizados",
    "elasticidades",
    "elipse_confianca",
    "nls",
    "stepwise",
    "pdl",
    "ardl",
    "ardl_bounds",
    "tar",
    "setar",
    "star",
]

