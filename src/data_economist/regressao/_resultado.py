"""
Resultados compartilhados para data_economist.regressao.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class RegResult:
    modelo: str
    params: pd.Series
    pvalues: pd.Series
    aic: float
    bic: float
    r2: float
    r2_adj: float
    resid: pd.Series
    fitted: pd.Series
    nobs: int
    extras: dict = field(default_factory=dict)
    fit_obj: Any = field(default=None, repr=False)


@dataclass
class NLSResult:
    params: pd.Series
    stderr: pd.Series
    pvalues: pd.Series
    resid: pd.Series
    fitted: pd.Series
    rmse: float
    nobs: int
    fit_obj: Any = field(default=None, repr=False)


@dataclass
class StepwiseResult:
    selecionadas: list[str]
    criterio_final: float
    historico: list[dict]
    resultado: RegResult


@dataclass
class ThresholdResult:
    threshold: float
    n_regime_1: int
    n_regime_2: int
    resultado_regime_1: RegResult
    resultado_regime_2: RegResult

