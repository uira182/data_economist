"""
Módulo X-13 (seasonal): dessazonalização via X-13ARIMA-SEATS.

Requer o binário X-13 no ambiente. Use x13.init() para garantir um venv
no projeto com x13binary instalado (diretório "venv" com o .exe dentro).
"""

from pathlib import Path
import subprocess
import sys


def _project_root(start: Path | None = None) -> Path:
    """Procura a raiz do projeto (onde está pyproject.toml ou src/data_economist)."""
    start = start or Path.cwd()
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
        if (parent / "src" / "data_economist").is_dir():
            return parent
    return start


def _venv_bin_name() -> str:
    """Nome do executável X-13 conforme a plataforma."""
    if sys.platform == "win32":
        return "x13as_html.exe"
    return "x13as"


def _venv_pip(venv_path: Path) -> Path:
    """Caminho do pip dentro do venv."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"


def _venv_x13_bin(venv_path: Path) -> Path:
    """Caminho do binário X-13 dentro do venv."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / _venv_bin_name()
    return venv_path / "bin" / _venv_bin_name()


def init(project_root: Path | str | None = None) -> Path:
    """
    Garante que existe um diretório "venv" no projeto com x13binary instalado
    (e portanto o executável X-13 dentro do venv).

    Se o venv não existir, é criado. Se x13binary não estiver instalado
    nesse venv, é instalado.

    Parâmetros
    ----------
    project_root : path ou str, opcional
        Raiz do projeto. Se None, é inferida (pyproject.toml ou src/data_economist).

    Devolve
    -------
    Path
        Caminho do diretório "venv" no projeto.
    """
    root = Path(project_root) if project_root else _project_root()
    venv_path = root / "venv"

    if not venv_path.is_dir():
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
        )

    pip_exe = _venv_pip(venv_path)
    if not pip_exe.is_file():
        raise FileNotFoundError(
            f"Pip do venv não encontrado: {pip_exe}. Recrie o venv com python -m venv {venv_path}"
        )

    # Instalar ou atualizar x13binary no venv (idempotente)
    subprocess.run(
        [str(pip_exe), "install", "x13binary"],
        check=True,
        capture_output=True,
    )

    x13_bin = _venv_x13_bin(venv_path)
    if not x13_bin.is_file():
        raise FileNotFoundError(
            f"Após instalar x13binary, o binário não foi encontrado em: {x13_bin}"
        )

    return venv_path


def get_x13_bin_path(project_root: Path | str | None = None) -> str:
    """
    Devolve o caminho do executável X-13.

    Procura primeiro no venv do projeto (diretório "venv"). Se não existir
    aí, usa x13binary.find_x13_bin() do ambiente atual.

    Parâmetros
    ----------
    project_root : path ou str, opcional
        Raiz do projeto. Se None, é inferida.

    Devolve
    -------
    str
        Caminho absoluto do executável (ex.: .../venv/Scripts/x13as_html.exe).
    """
    root = Path(project_root) if project_root else _project_root()
    venv_bin = _venv_x13_bin(root / "venv")
    if venv_bin.is_file():
        return str(venv_bin.resolve())

    try:
        import x13binary
        path = x13binary.find_x13_bin()
        if path and Path(path).is_file():
            return path
    except ImportError:
        pass

    raise FileNotFoundError(
        "Binário X-13 não encontrado. Execute x13.init() para criar o venv do projeto "
        "e instalar x13binary, ou instale x13binary no ambiente atual: pip install x13binary"
    )


# API seasonal (seas, final, trend, irregular, original, summary, get_series, udg)
from .seas import SeasonalResult, seas


def final(model: SeasonalResult):
    """Série dessazonalizada (ajustada)."""
    return model.final


def trend(model: SeasonalResult):
    """Componente tendência."""
    return model.trend


def irregular(model: SeasonalResult):
    """Componente irregular."""
    return model.irregular


def original(model: SeasonalResult):
    """Série original."""
    return model.original


def udg(model: SeasonalResult):
    """Diagnósticos (conteúdo do .udg)."""
    return model.udg


from .output import get_series, summary

__all__ = [
    "init",
    "get_x13_bin_path",
    "seas",
    "SeasonalResult",
    "final",
    "trend",
    "irregular",
    "original",
    "udg",
    "get_series",
    "summary",
]
