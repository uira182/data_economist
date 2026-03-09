"""
conftest.py — fixtures compartilhadas entre todos os arquivos de teste.

As fixtures deste arquivo são descobertas automaticamente pelo pytest e
ficam disponíveis sem necessidade de import em qualquer test_*.py do projeto.

Organização
-----------
- Fixtures de séries mock com propriedades matemáticas conhecidas (MockSeries)
- Fixtures simples de pd.Series para testes de forma/tipo
- sys.path configurado uma única vez para o src-layout do projeto
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Garante que src/ está no path para todos os arquivos de teste
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tests.mock_series import (
    MockSeries,
    fazer_ar1,
    fazer_constante,
    fazer_serie_completa,
    fazer_serie_diaria,
    fazer_sazonal_pura,
    fazer_tendencia_linear,
)


# ---------------------------------------------------------------------------
# Fixtures de MockSeries (com resultados esperados embutidos)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mock_tendencia_linear() -> MockSeries:
    """
    Tendência linear pura: y_t = 100 + 0.5*t, sem ruído.

    Usar para validar:
    - hp(): ciclo deve ser ≈ 0
    - hp(): tendencia deve correlacionar > 0.999 com original
    - para_frequencia(): valores agregados dentro do range esperado
    """
    return fazer_tendencia_linear()


@pytest.fixture(scope="session")
def mock_constante() -> MockSeries:
    """
    Série constante: y_t = 50 para todo t.

    Usar para validar:
    - hp(): ciclo deve ser zero exato
    - ses(): suavizado deve ser 50 dentro de tolerância mínima
    - holt(): idem
    - para_frequencia(): conserva o valor em qualquer frequência/método
    """
    return fazer_constante()


@pytest.fixture(scope="session")
def mock_ar1() -> MockSeries:
    """
    Processo AR(1): y_t = 0.8*y_{t-1} + e_t, seed=42, n=120.

    Usar para validar:
    - whitening(lags=1): coeficiente AR estimado ≈ 0.8 (± 0.15)
    - whitening(): resíduos com variância menor que a série original
    """
    return fazer_ar1()


@pytest.fixture(scope="session")
def mock_sazonal_pura() -> MockSeries:
    """
    Sazonal pura: y_t = 100 + 10*sin(2*pi*t/12), sem tendência, sem ruído.

    Usar para validar:
    - bk(): ciclo extraído deve correlacionar > 0.90 com a série original
    - cf(): idem
    - holt_winters(): deve detectar sazonalidade forte (gamma alto)
    - média da série deve ser ≈ 100
    """
    return fazer_sazonal_pura()


@pytest.fixture(scope="session")
def mock_serie_completa() -> MockSeries:
    """
    Série completa: y_t = 100 + 0.5*t + 8*sin(2*pi*t/12) + ruído(σ=0.5).

    Representa o caso de uso típico (série econômica mensal).
    Usar para validar o fluxo completo de análise.
    """
    return fazer_serie_completa()


@pytest.fixture(scope="session")
def mock_serie_diaria() -> MockSeries:
    """
    Série diária: y_t = 200 + 0.1*t + ruído, n=365.

    Usar para validar conversão alta→baixa de frequência.
    """
    return fazer_serie_diaria()


# ---------------------------------------------------------------------------
# Fixtures simples de pd.Series (mantidas para compatibilidade)
# ---------------------------------------------------------------------------

@pytest.fixture
def serie_mensal():
    """Série mensal sintética genérica (72 obs). Para testes de forma/tipo."""
    idx = pd.date_range("2015-01", periods=72, freq="ME")
    valores = [
        100 + i * 0.5 + 10 * (1 if i % 12 in (5, 6, 7) else (-3 if i % 12 in (11, 0, 1) else 0))
        for i in range(72)
    ]
    return pd.Series(valores, index=idx, name="serie_teste", dtype=float)


@pytest.fixture
def serie_trimestral():
    """Série trimestral sintética (24 obs). Para testes de forma/tipo."""
    idx = pd.date_range("2015-01", periods=24, freq="QE")
    valores = [200 + i * 1.2 + 5 * (1 if i % 4 in (1, 2) else -2) for i in range(24)]
    return pd.Series(valores, index=idx, name="serie_trim", dtype=float)


@pytest.fixture
def serie_diaria():
    """Série diária sintética (365 obs). Para testes de forma/tipo."""
    idx = pd.date_range("2020-01-01", periods=365, freq="D")
    valores = [50 + i * 0.05 for i in range(365)]
    return pd.Series(valores, index=idx, name="serie_diaria", dtype=float)


@pytest.fixture
def serie_sem_indice():
    """Série sem DatetimeIndex — deve levantar ValueError."""
    return pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
