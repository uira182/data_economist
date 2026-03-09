"""
Selecao de variaveis (stepwise).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._resultado import StepwiseResult
from .linear import ols


def _score(res, criterio):
    return res.aic if criterio == "aic" else res.bic


def stepwise(y, X, metodo="forward", criterio="aic", max_vars=None):
    """
    Stepwise simples com criterio AIC/BIC.
    """
    metodo = metodo.lower()
    criterio = criterio.lower()
    if metodo not in {"forward", "backward", "both"}:
        raise ValueError("metodo invalido")
    if criterio not in {"aic", "bic"}:
        raise ValueError("criterio invalido")

    X_df = pd.DataFrame(X).copy()
    if X_df.shape[1] == 0:
        raise ValueError("X sem variaveis")
    all_vars = list(X_df.columns)
    selected = [] if metodo in {"forward", "both"} else all_vars.copy()
    history = []
    improved = True

    if max_vars is None:
        max_vars = len(all_vars)

    while improved:
        improved = False
        candidates = []

        # Add step
        if metodo in {"forward", "both"} and len(selected) < max_vars:
            remaining = [v for v in all_vars if v not in selected]
            for v in remaining:
                trial = selected + [v]
                res = ols(y, X_df[trial], add_const=True)
                candidates.append(("add", v, trial, _score(res, criterio), res))

        # Remove step
        if metodo in {"backward", "both"} and len(selected) > 1:
            for v in selected:
                trial = [z for z in selected if z != v]
                res = ols(y, X_df[trial], add_const=True)
                candidates.append(("drop", v, trial, _score(res, criterio), res))

        if not candidates:
            break

        candidates.sort(key=lambda x: x[3])
        best_action, best_var, best_trial, best_score, best_res = candidates[0]
        if len(history) == 0 or best_score < history[-1]["score"] - 1e-8:
            selected = best_trial
            history.append(
                {
                    "acao": best_action,
                    "variavel": best_var,
                    "selecionadas": selected.copy(),
                    "score": float(best_score),
                }
            )
            improved = True

    if not selected:
        selected = [all_vars[0]]
    final = ols(y, X_df[selected], add_const=True)
    return StepwiseResult(
        selecionadas=selected,
        criterio_final=float(_score(final, criterio)),
        historico=history,
        resultado=final,
    )

