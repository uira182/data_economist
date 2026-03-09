"""
Constrói o ficheiro .spc (especificação) para o X-13ARIMA-SEATS.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd


def _normalize_arima_model(arima_model: str) -> str:
    """
    Normaliza modelo ARIMA para o formato esperado pelo X-13.

    Exemplos aceites:
      - "(1 0 1)(1 0 1)"
      - "((1 0 1)(1 0 1))"
      - " ( 1 0 1 ) ( 1 0 1 ) "
    Devolve sempre:
      - "(1 0 1)(1 0 1)"
    """
    model = " ".join(arima_model.strip().split())
    # Remover apenas um par de parênteses externos, se envolver o modelo todo
    if model.startswith("((") and model.endswith("))"):
        model = model[1:-1].strip()
    return model


def _infer_freq(series: pd.Series) -> str:
    """Inferir frequência (monthly/quarterly) a partir do índice."""
    if not isinstance(series.index, pd.DatetimeIndex):
        return "monthly"
    infer = pd.infer_freq(series.index)
    if infer and "Q" in (infer or ""):
        return "quarterly"
    return "monthly"


def _series_start(series: pd.Series, freq: str) -> str:
    """Formato start para o .spc: 2020.01 (mensal) ou 2020.1 (trimestral)."""
    idx = series.index
    if isinstance(idx, pd.DatetimeIndex):
        first = idx.min()
        if freq == "quarterly":
            return f"{first.year}.{(first.month - 1) // 3 + 1}"
        return f"{first.year}.{first.month:02d}"
    # índice inteiro tipo período
    return "1.1"


def _format_data(series: pd.Series) -> str:
    """Valores da série em blocos, como no .spc."""
    vals = series.astype(float).dropna().tolist()
    lines = []
    for i in range(0, len(vals), 12):
        chunk = vals[i : i + 12]
        lines.append("  " + " ".join(f"{x:.6g}" for x in chunk))
    return "\n".join(lines) if lines else "  "


def build_spec(
    series: pd.Series,
    *,
    title: str = "series",
    transform_function: str = "auto",
    automdl: bool = True,
    arima_model: str | None = None,
    outlier: bool = True,
    regression_aictest: list[str] | None = None,
    estimate_maxiter: int | None = None,
    estimate_tol: float | None = None,
    **kwargs: Any,
) -> str:
    """
    Gera o conteúdo do ficheiro .spc para o X-13.

    Parâmetros
    ----------
    series : pandas.Series
        Série temporal com DatetimeIndex (mensal ou trimestral).
    title : str
        Título da série no .spc.
    transform_function : str
        "auto", "log" ou "none".
    automdl : bool
        Se True, seleção automática do modelo ARIMA.
    arima_model : str, opcional
        Modelo fixo, ex. "(0 1 1)(0 1 1)".
    outlier : bool
        Deteção automática de outliers.
    regression_aictest : list, opcional
        Ex. ["td", "easter"].
    estimate_maxiter, estimate_tol : opcionais
        Controle da estimação.

    Devolve
    -------
    str
        Conteúdo do ficheiro .spc.
    """
    freq = _infer_freq(series)
    start = _series_start(series, freq)
    data_block = _format_data(series)

    parts = [
        "series{",
        f'  title="{title}"',
        f"  start={start}",
        "  data=(",
        data_block,
        "  )",
        "}",
        "",
        "spectrum{",
        "  savelog=peaks",
        "}",
        "",
        "transform{",
        f"  function={transform_function}",
        "}",
    ]

    if regression_aictest:
        aic = " ".join(regression_aictest)
        parts += ["", "regression{", f"  aictest=({aic})", "}"]

    if automdl and not arima_model:
        parts += ["", "automdl{", "}"]
    elif arima_model:
        model = _normalize_arima_model(arima_model)
        parts += ["", "arima{", f"  model={model}", "}"]

    if outlier:
        parts += ["", "outlier{", "}"]

    if estimate_maxiter is not None:
        parts += ["", "estimate{"]
        parts.append(f"  maxiter={estimate_maxiter}")
        if estimate_tol is not None:
            parts.append(f"  tol={estimate_tol}")
        parts += ["}"]

    # SEATS: pedir tabelas s11 (ajustada), s12 (tendência), s13 (irregular) no output
    # save= gera arquivos de texto com precisão total (io.s11, io.s12, io.s13)
    # evita truncamento de casas decimais no HTML para séries de pequena magnitude
    parts += [
        "",
        "seats{",
        "  print=(s11 s12 s13)",
        "  save=(s11 s12 s13)",
        "}",
    ]
    return "\n".join(parts)


def write_spec(content: str, path: Path | str) -> Path:
    """Escreve o conteúdo .spc no ficheiro path."""
    path = Path(path)
    path.write_text(content, encoding="utf-8")
    return path
