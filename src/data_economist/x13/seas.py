"""
Função principal seas() e objeto SeasonalResult.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from . import get_x13_bin_path
from .parser import parse_output, parse_udg
from .runner import run_x13
from .spec_builder import build_spec, write_spec


class SeasonalResult:
    """
    Resultado do ajuste sazonal X-13 (equivalente ao objeto devolvido por seas() no R).
    """

    def __init__(
        self,
        original: pd.Series,
        final: pd.Series | None = None,
        trend: pd.Series | None = None,
        irregular: pd.Series | None = None,
        udg: dict[str, Any] | None = None,
        messages: list[str] | None = None,
        spc_content: str | None = None,
        work_dir: Path | str | None = None,
        base_name: str = "io",
    ):
        self._original = original
        self._final = final if final is not None else original.copy()
        self._trend = trend
        self._irregular = irregular
        self._udg = udg or {}
        self._messages = messages or []
        self._spc_content = spc_content
        self._work_dir = Path(work_dir) if work_dir else None
        self._base_name = base_name

    @property
    def original(self) -> pd.Series:
        """Série original."""
        return self._original

    @property
    def final(self) -> pd.Series:
        """Série dessazonalizada (ajustada)."""
        return self._final

    @property
    def trend(self) -> pd.Series | None:
        """Componente tendência."""
        return self._trend

    @property
    def irregular(self) -> pd.Series | None:
        """Componente irregular."""
        return self._irregular

    @property
    def udg(self) -> dict[str, Any]:
        """Diagnósticos (conteúdo do .udg)."""
        return self._udg

    @property
    def messages(self) -> list[str]:
        """Mensagens e avisos do X-13."""
        return self._messages

    @property
    def spc_content(self) -> str | None:
        """Conteúdo do ficheiro .spc usado."""
        return self._spc_content

    @property
    def work_dir(self) -> Path | None:
        """Directório de trabalho do X-13 (contém io.html, io.udg, etc.). Útil para debug."""
        return self._work_dir


def seas(
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
    x13_bin_path: str | None = None,
    **kwargs: Any,
) -> SeasonalResult:
    """
    Ajuste sazonal X-13ARIMA-SEATS (equivalente a seas() no R).

    Gera o .spc, corre o binário X-13, lê os outputs e devolve um SeasonalResult
    com série original, série ajustada (final), tendência, irregular e diagnósticos.

    Parâmetros
    ----------
    series : pandas.Series
        Série temporal com DatetimeIndex (mensal ou trimestral).
    title : str
        Título da série no ficheiro .spc.
    transform_function : str
        "auto", "log" ou "none".
    automdl : bool
        Seleção automática do modelo ARIMA.
    arima_model : str, opcional
        Modelo fixo, ex. "(0 1 1)(0 1 1)".
    outlier : bool
        Deteção automática de outliers.
    regression_aictest : list, opcional
        Ex. ["td", "easter"].
    estimate_maxiter, estimate_tol : opcionais
        Controle da estimação.
    x13_bin_path : str, opcional
        Caminho do executável X-13. Se None, usa get_x13_bin_path().

    Devolve
    -------
    SeasonalResult
    """
    content = build_spec(
        series,
        title=title,
        transform_function=transform_function,
        automdl=automdl,
        arima_model=arima_model,
        outlier=outlier,
        regression_aictest=regression_aictest,
        estimate_maxiter=estimate_maxiter,
        estimate_tol=estimate_tol,
        **kwargs,
    )
    work_dir = Path(tempfile.mkdtemp())
    base = "io"
    spc_path = work_dir / f"{base}.spc"
    write_spec(content, spc_path)

    run_work_dir, stdout, stderr = run_x13(
        spc_path,
        work_dir=work_dir,
        x13_bin_path=x13_bin_path,
        store_diagnostics=True,
    )
    parsed = parse_output(run_work_dir, base, series)
    messages = list(parsed.get("messages", []))
    if stdout.strip():
        for line in stdout.strip().splitlines():
            if line.strip():
                messages.append(line)
    if stderr.strip():
        for line in stderr.strip().splitlines():
            if line.strip():
                messages.append(line)

    return SeasonalResult(
        original=parsed["original"],
        final=parsed["final"],
        trend=parsed.get("trend"),
        irregular=parsed.get("irregular"),
        udg=parsed.get("udg", {}),
        messages=messages,
        spc_content=content,
        work_dir=run_work_dir,
        base_name=base,
    )
