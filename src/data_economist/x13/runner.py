"""
Executa o binário X-13ARIMA-SEATS (subprocess) num diretório de trabalho.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def run_x13(
    spc_path: Path | str,
    work_dir: Path | str | None = None,
    x13_bin_path: str | None = None,
    store_diagnostics: bool = True,
) -> tuple[Path, str, str]:
    """
    Corre o X-13 com o ficheiro .spc dado.

    Parâmetros
    ----------
    spc_path : path
        Ficheiro .spc (com ou sem extensão).
    work_dir : path, opcional
        Diretório de trabalho (onde estão/criados .out, .udg, etc.).
        Se None, usa o diretório do spc_path.
    x13_bin_path : str, opcional
        Caminho do executável X-13. Se None, usa get_x13_bin_path().
    store_diagnostics : bool
        Passar -s para gravar ficheiro de diagnósticos (.udg).

    Devolve
    -------
    (work_dir, stdout, stderr)
    """
    spc_path = Path(spc_path).resolve()
    if not spc_path.suffix:
        spc_path = spc_path.with_suffix(".spc")
    if not spc_path.is_file():
        raise FileNotFoundError(f"Ficheiro .spc não encontrado: {spc_path}")

    work_dir = Path(work_dir) if work_dir else spc_path.parent
    work_dir = work_dir.resolve()

    if x13_bin_path is None:
        from . import get_x13_bin_path
        x13_bin_path = get_x13_bin_path()

    # Basename sem extensão: x13as procura base.spc e escreve base.out em work_dir
    base = spc_path.stem
    cmd = [x13_bin_path, "-i", base, "-o", base]
    if store_diagnostics:
        cmd.append("-s")

    proc = subprocess.run(
        cmd,
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=300,
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    if proc.returncode != 0:
        extra = [f"X-13 terminou com código {proc.returncode}."]
        if stdout.strip():
            extra.append("stdout:\n" + stdout.strip())
        if stderr.strip():
            extra.append("stderr:\n" + stderr.strip())
        stderr = "\n".join(extra)
    return work_dir, stdout, stderr
