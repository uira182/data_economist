"""
Resumo em texto do resultado X-13 (equivalente a summary(m) no R).
"""

from __future__ import annotations

from typing import Any


def summary(model: Any) -> str:
    """
    Devolve um resumo em texto do ajuste sazonal (modelo, diagnósticos principais).

    Parâmetros
    ----------
    model : SeasonalResult
        Resultado de x13.seas().
    """
    lines = [
        "X-13ARIMA-SEATS Seasonal Adjustment Result",
        "==========================================",
        "",
        f"Original:  {len(model.original)} obs, span {model.original.index.min()} to {model.original.index.max()}",
        f"Final:     {len(model.final)} obs (dessazonalizada)",
        "",
    ]
    udg = model.udg
    if udg:
        lines.append("Diagnósticos (udg):")
        for k in ("nobs", "transform", "automdl", "arimamdl", "converged", "aic", "bic"):
            if k in udg:
                lines.append(f"  {k}: {udg[k]}")
        best = udg.get("automdl.best5.mdl01") or udg.get("automdl.first")
        if best:
            lines.append(f"  best model: {best}")
    if model.messages:
        lines.append("")
        lines.append("Mensagens:")
        for m in model.messages[:10]:
            lines.append(f"  - {m[:80]}")
    return "\n".join(lines)
