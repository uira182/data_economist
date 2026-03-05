"""Testes básicos do pacote data_economist."""

import pytest


def test_import_package():
    """O pacote data_economist pode ser importado."""
    import data_economist
    assert data_economist is not None


def test_version_exists():
    """O pacote expõe __version__."""
    import data_economist
    assert hasattr(data_economist, "__version__")
    assert isinstance(data_economist.__version__, str)
    assert len(data_economist.__version__) >= 5  # e.g. "0.1.0"


def test_import_ibge():
    """from data_economist import ibge expõe o módulo ibge com .url() e .get()."""
    import data_economist
    assert hasattr(data_economist, "ibge")
    assert hasattr(data_economist.ibge, "url")
    assert hasattr(data_economist.ibge, "get")
