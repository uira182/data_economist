"""
modelos/_resultado.py — Dataclasses de resultado compartilhadas do módulo modelos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd


@dataclass
class ModeloResult:
    """Resultado de um modelo de série temporal estimado."""

    modelo: str
    params: pd.Series
    pvalues: pd.Series
    aic: float
    bic: float
    hqic: float
    log_likelihood: float
    residuos: pd.Series
    fitted: pd.Series
    nobs: int
    ordem: tuple
    _fit: Any = field(default=None, repr=False)

    def __repr__(self) -> str:
        sig = (self.params[self.pvalues < 0.05].index.tolist())
        return (
            f"ModeloResult({self.modelo}  AIC={self.aic:.2f}  BIC={self.bic:.2f}"
            f"  nobs={self.nobs}  sig={sig})"
        )


@dataclass
class PrevisaoResult:
    """Resultado de previsão fora da amostra."""

    valores: pd.Series
    ic_lower: pd.Series
    ic_upper: pd.Series
    steps: int
    alpha: float = 0.05

    def __repr__(self) -> str:
        return (
            f"PrevisaoResult(steps={self.steps}  alpha={self.alpha}"
            f"  [{self.valores.index[0].date()} .. {self.valores.index[-1].date()}])"
        )


@dataclass
class RaizResult:
    """Resultado de teste de raiz unitária."""

    statistic: float
    pvalue: float
    lags: int
    metodo: str
    hipotese_nula: str
    conclusao: str
    rejeita_h0: bool
    alpha: float = 0.05
    criticos: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"RaizResult({self.metodo}  stat={self.statistic:.4f}"
            f"  p={self.pvalue:.4f}  rejeita_h0={self.rejeita_h0})"
        )


@dataclass
class ACFResult:
    """Resultado de autocorrelação e autocorrelação parcial."""

    acf: np.ndarray
    pacf: np.ndarray
    ic_acf: np.ndarray
    ic_pacf: np.ndarray
    nlags: int
    ljung_box: pd.DataFrame

    def __repr__(self) -> str:
        return f"ACFResult(nlags={self.nlags})"


def _concluir_raiz(pvalue: float, metodo: str, h0: str, alpha: float) -> tuple[str, bool]:
    rejeita = bool(pvalue < alpha)
    if rejeita:
        conclusao = f"{metodo}: rejeita H0 (p={pvalue:.4f} < {alpha}) — {h0} rejeitada."
    else:
        conclusao = f"{metodo}: nao rejeita H0 (p={pvalue:.4f} >= {alpha}) — {h0} nao rejeitada."
    return conclusao, rejeita
