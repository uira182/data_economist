"""
Fábrica de séries sintéticas com propriedades matemáticas conhecidas.

Cada MockSeries carrega:
  - series     : pd.Series pronta para passar às funções do módulo tratamento
  - descricao  : o que a série representa e como foi construída
  - expected   : dict com os valores esperados nos resultados, usados para
                 validação numérica nos testes

Por que isso importa
--------------------
Testes que só verificam tipos e formas ("retornou um pd.Series?") não detectam
regressões nos cálculos. Com séries de propriedades conhecidas é possível
afirmar, por exemplo, que o ciclo do HP sobre uma tendência linear pura deve
ser ≈ 0, ou que o whitening de um AR(1) com coeficiente 0.8 deve recuperar
esse coeficiente dentro de uma tolerância razoável.

Uso
---
    from tests.mock_series import fazer_tendencia_linear, fazer_ar1, ...

    mock = fazer_tendencia_linear()
    resultado = hp(mock.series)
    assert abs(resultado.ciclo).max() < mock.expected["ciclo_max_abs"]
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class MockSeries:
    """
    Série sintética com propriedades matemáticas conhecidas.

    Atributos
    ---------
    series : pd.Series
        Série com DatetimeIndex mensal (padrão) pronta para uso.
    descricao : str
        Descrição da construção matemática da série.
    expected : dict
        Valores de referência para validação numérica. As chaves seguem o
        padrão <funcao>_<atributo> para deixar claro qual resultado valida qual.
        Ex.: "hp_ciclo_max_abs", "ses_alpha_range", "whitening_coef_ar1".
    seed : int
        Semente usada para geração de ruído (garante determinismo).
    """

    series: pd.Series
    descricao: str
    expected: dict[str, Any] = field(default_factory=dict)
    seed: int = 42


# ---------------------------------------------------------------------------
# 1. Tendência linear pura — sem sazonalidade, sem ruído
# ---------------------------------------------------------------------------

def fazer_tendencia_linear(
    n: int = 72,
    inicio: str = "2015-01",
    a: float = 100.0,
    b: float = 0.5,
) -> MockSeries:
    """
    y_t = a + b * t   (t = 0, 1, ..., n-1)

    Propriedades esperadas
    ----------------------
    - HP com qualquer lambda: tendencia ≈ y_t (correlação > 0.999)
    - HP com qualquer lambda: ciclo ≈ 0 (|max| < 2.0 para n=72)
    - SES: não captura tendência, suavizado fica abaixo dos valores reais
    - Para_frequencia (agregação): conserva a média por período
    """
    idx = pd.date_range(inicio, periods=n, freq="ME")
    t = np.arange(n, dtype=float)
    valores = a + b * t
    series = pd.Series(valores, index=idx, name="tendencia_linear")

    return MockSeries(
        series=series,
        descricao=f"Tendência linear pura: y_t = {a} + {b}*t, sem ruído.",
        expected={
            # HP
            "hp_ciclo_max_abs": 2.0,          # ciclo deve ser próximo de zero
            "hp_tendencia_corr_min": 0.999,   # tendência deve seguir a série
            # Conversão: média mensal agregada para trimestral deve estar no range
            "freq_valor_min": a,
            "freq_valor_max": a + b * (n - 1),
        },
    )


# ---------------------------------------------------------------------------
# 2. Série constante — caso trivial de referência
# ---------------------------------------------------------------------------

def fazer_constante(
    n: int = 72,
    inicio: str = "2015-01",
    valor: float = 50.0,
) -> MockSeries:
    """
    y_t = valor   para todo t

    Propriedades esperadas
    ----------------------
    - HP: ciclo = 0 exato, tendencia = valor exato
    - SES: suavizado = valor exato (independente de alpha)
    - Holt: suavizado = valor exato
    - Whitening: série branca = 0 (resíduos nulos após remoção da constante)
    - Para_frequencia: conserva o valor em qualquer frequência e método
    """
    idx = pd.date_range(inicio, periods=n, freq="ME")
    series = pd.Series([valor] * n, index=idx, name="constante", dtype=float)

    return MockSeries(
        series=series,
        descricao=f"Série constante: y_t = {valor} para todo t.",
        expected={
            # HP
            "hp_ciclo_max_abs": 1e-8,
            "hp_tendencia_valor": valor,
            # SES / Holt
            "ses_suavizado_max_desvio": 1e-3,
            "holt_suavizado_max_desvio": 1e-3,
            # Frequência
            "freq_valor_esperado": valor,
        },
    )


# ---------------------------------------------------------------------------
# 3. Série AR(1) — coeficiente conhecido
# ---------------------------------------------------------------------------

def fazer_ar1(
    n: int = 120,
    inicio: str = "2010-01",
    phi: float = 0.8,
    sigma: float = 1.0,
    seed: int = 42,
) -> MockSeries:
    """
    y_t = phi * y_{t-1} + e_t,   e_t ~ N(0, sigma^2)

    Propriedades esperadas
    ----------------------
    - Whitening com lags=1: coeficiente AR estimado ≈ phi (± tolerância)
    - Whitening: resíduos devem ter autocorrelação baixa (série branca)
    - HP com lambda alto: captura a "pseudotendência" estocástica
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(inicio, periods=n, freq="ME")
    y = np.zeros(n)
    e = rng.normal(0, sigma, n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + e[t]
    series = pd.Series(y, index=idx, name="ar1")

    # tolerância: em 120 obs, a estimação MQO do phi deve ser ± 0.15
    tol = 0.15
    return MockSeries(
        series=series,
        descricao=(
            f"Processo AR(1): y_t = {phi}*y_{{t-1}} + e_t, "
            f"e_t ~ N(0, {sigma}^2), seed={seed}."
        ),
        expected={
            "whitening_coef_ar1_valor": phi,
            "whitening_coef_ar1_tol": tol,
            "whitening_lags_esperados": 1,
        },
        seed=seed,
    )


# ---------------------------------------------------------------------------
# 4. Série sazonal pura — onda senoidal, sem tendência, sem ruído
# ---------------------------------------------------------------------------

def fazer_sazonal_pura(
    n: int = 96,
    inicio: str = "2015-01",
    amplitude: float = 10.0,
    periodo: int = 12,
    nivel: float = 100.0,
) -> MockSeries:
    """
    y_t = nivel + amplitude * sin(2*pi*t / periodo)

    Propriedades esperadas
    ----------------------
    - BK com [periodo*0.5, periodo*2]: ciclo deve ser altamente correlacionado
      com a série original (correlação > 0.90)
    - CF: idem ao BK
    - HP com lambda grande: tendencia ≈ nivel (constante), ciclo ≈ sinal sazonal
    - Holt-Winters: gamma deve ser estimado alto (sazonalidade forte)
    - A média da série deve ser ≈ nivel (sin tem média 0)
    """
    idx = pd.date_range(inicio, periods=n, freq="ME")
    t = np.arange(n, dtype=float)
    valores = nivel + amplitude * np.sin(2 * math.pi * t / periodo)
    series = pd.Series(valores, index=idx, name="sazonal_pura")

    return MockSeries(
        series=series,
        descricao=(
            f"Sazonal pura: y_t = {nivel} + {amplitude}*sin(2*pi*t/{periodo}), "
            "sem tendência, sem ruído."
        ),
        expected={
            # BK / CF
            "bk_ciclo_corr_min": 0.90,    # ciclo extraído deve correlacionar com original
            # HP com lambda grande isola o nível
            "hp_tendencia_media_esperada": nivel,
            "hp_tendencia_desvio_max": amplitude * 0.5,
            # Média da série
            "media_esperada": nivel,
            "media_tol": 0.5,
            # Amplitude da série
            "amplitude_max": nivel + amplitude,
            "amplitude_min": nivel - amplitude,
        },
    )


# ---------------------------------------------------------------------------
# 5. Série completa — tendência + sazonalidade + ruído pequeno
# ---------------------------------------------------------------------------

def fazer_serie_completa(
    n: int = 72,
    inicio: str = "2015-01",
    a: float = 100.0,
    b: float = 0.5,
    amplitude_sazonal: float = 8.0,
    sigma_ruido: float = 0.5,
    seed: int = 42,
) -> MockSeries:
    """
    y_t = a + b*t + amplitude*sin(2*pi*t/12) + e_t,   e_t ~ N(0, sigma^2)

    Representa o caso de uso típico: série econômica mensal com tendência de
    crescimento, sazonalidade anual clara e pequeno ruído idiossincrático.

    Propriedades esperadas
    ----------------------
    - HP: tendencia correlaciona com (a + b*t), ciclo captura a sazonalidade
    - Holt-Winters aditivo: ajuste com m=12 deve ter AIC finito e boa cobertura
    - ETS auto: deve selecionar modelo com tendência aditiva e sazonalidade
    - BK [6, 18]: ciclo correlaciona com o componente sazonal verdadeiro
    - Para_frequencia (mensal→trimestral, mean): valores na faixa esperada
    - Whitening: remove autocorrelação, residuos com std menor que série original
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(inicio, periods=n, freq="ME")
    t = np.arange(n, dtype=float)
    tendencia = a + b * t
    sazonal = amplitude_sazonal * np.sin(2 * math.pi * t / 12)
    ruido = rng.normal(0, sigma_ruido, n)
    valores = tendencia + sazonal + ruido
    series = pd.Series(valores, index=idx, name="serie_completa", dtype=float)

    # componentes verdadeiros para comparação
    tendencia_series = pd.Series(tendencia, index=idx, name="tendencia_verdadeira")
    sazonal_series = pd.Series(sazonal, index=idx, name="sazonal_verdadeira")

    return MockSeries(
        series=series,
        descricao=(
            f"Série completa: y_t = {a} + {b}*t + {amplitude_sazonal}*sin(...) + e_t, "
            f"sigma_ruido={sigma_ruido}, seed={seed}."
        ),
        expected={
            # HP
            "hp_tendencia_corr_com_linear": 0.99,  # tendencia HP vs tendência verdadeira
            # Holt-Winters
            "hw_aic_finito": True,
            "hw_gamma_positivo": True,
            # Whitening
            "whitening_std_ratio_max": 0.9,  # std(branca) / std(original) < 0.9
            # Frequência: mensal para trimestral
            "freq_trimestral_len": n // 3,
            "freq_valor_min": a - amplitude_sazonal - 3 * sigma_ruido,
            "freq_valor_max": a + b * (n - 1) + amplitude_sazonal + 3 * sigma_ruido,
        },
        seed=seed,
    )


# ---------------------------------------------------------------------------
# 6. Série diária — para testes de conversão de frequência
# ---------------------------------------------------------------------------

def fazer_serie_diaria(
    n: int = 365,
    inicio: str = "2020-01-01",
    a: float = 200.0,
    b: float = 0.1,
    seed: int = 42,
) -> MockSeries:
    """
    y_t = a + b*t + e_t,   e_t ~ N(0, 0.5^2)

    Série diária com tendência suave. Usada para testar a conversão
    alta→baixa (diário→mensal, diário→trimestral).

    Propriedades esperadas
    ----------------------
    - Para_frequencia mensal (mean): ~12 valores, média próxima da linha de tendência
    - Para_frequencia trimestral (sum): ~4 valores, soma conservada por período
    - Para_frequencia mensal → diário (linear): interpolação dentro do range original
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(inicio, periods=n, freq="D")
    t = np.arange(n, dtype=float)
    valores = a + b * t + rng.normal(0, 0.5, n)
    series = pd.Series(valores, index=idx, name="serie_diaria", dtype=float)

    return MockSeries(
        series=series,
        descricao=f"Série diária: y_t = {a} + {b}*t + ruído, n={n}.",
        expected={
            "freq_mensal_len_aprox": 12,
            "freq_valor_min": a - 5,
            "freq_valor_max": a + b * n + 5,
            "freq_interpolacao_dentro_range": True,
        },
        seed=seed,
    )


# ---------------------------------------------------------------------------
# Catálogo: todas as séries disponíveis com um dict de fácil acesso
# ---------------------------------------------------------------------------

def catalogo() -> dict[str, MockSeries]:
    """
    Retorna todas as séries mock disponíveis indexadas por nome.

    Uso
    ---
        from tests.mock_series import catalogo
        mocks = catalogo()
        series = mocks["tendencia_linear"].series
    """
    return {
        "tendencia_linear": fazer_tendencia_linear(),
        "constante": fazer_constante(),
        "ar1": fazer_ar1(),
        "sazonal_pura": fazer_sazonal_pura(),
        "serie_completa": fazer_serie_completa(),
        "serie_diaria": fazer_serie_diaria(),
    }
