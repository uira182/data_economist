"""
modelos/selecao.py — Seleção de modelos e diagnósticos de autocorrelação.

Funções
-------
auto_arima(serie, ...)          Seleciona melhor ARIMA/SARIMA por busca
criterios(serie, ordens, ...)   Tabela comparativa AIC/BIC/HQIC por ordem
acf_pacf(serie, ...)            ACF, PACF, ICs e Ljung-Box
"""

from __future__ import annotations

import itertools
import warnings
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from ._resultado import ACFResult, ModeloResult
from .arima import arima as _arima, sarima as _sarima


# ---------------------------------------------------------------------------
# auto_arima
# ---------------------------------------------------------------------------

def auto_arima(
    serie: pd.Series,
    *,
    max_p: int = 5,
    max_q: int = 5,
    max_d: int = 2,
    max_P: int = 2,
    max_Q: int = 2,
    max_D: int = 1,
    m: int = 1,
    criterio: str = "aic",
    stepwise: bool = True,
    trend: str = "n",
    verbose: bool = False,
) -> ModeloResult:
    """
    Seleciona automaticamente o melhor ARIMA(p,d,q) ou SARIMA(p,d,q)(P,D,Q)[m].

    Parâmetros
    ----------
    serie    : pd.Series com índice datetime
    max_p    : máximo para p (AR não-sazonal)
    max_q    : máximo para q (MA não-sazonal)
    max_d    : máximo para d (diferenças)
    max_P    : máximo para P (AR sazonal) — ignorado se m=1
    max_Q    : máximo para Q (MA sazonal) — ignorado se m=1
    max_D    : máximo para D (diferenças sazonais) — ignorado se m=1
    m        : periodicidade sazonal (1=sem sazonalidade, 12=mensal, 4=trimestral)
    criterio : 'aic' | 'bic' | 'hqic'
    stepwise : True → busca stepwise (mais rápida); False → busca exaustiva
    trend    : 'n' | 'c' | 'ct'
    verbose  : imprime progresso

    Retorna ModeloResult do melhor modelo encontrado
    """
    crit = criterio.lower()
    if crit not in ("aic", "bic", "hqic"):
        raise ValueError("criterio deve ser 'aic', 'bic' ou 'hqic'")

    if stepwise:
        return _auto_stepwise(serie, max_p, max_q, max_d, max_P, max_Q, max_D, m, crit, trend, verbose)
    return _auto_exaustivo(serie, max_p, max_q, max_d, max_P, max_Q, max_D, m, crit, trend, verbose)


def _valor_criterio(resultado: ModeloResult, crit: str) -> float:
    return getattr(resultado, crit)


def _tentar_modelo(serie, p, d, q, P, D, Q, m, trend):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if m > 1:
                return _sarima(serie, p, d, q, P, D, Q, m, trend=trend)
            return _arima(serie, p, d, q, trend=trend)
    except Exception:
        return None


def _auto_exaustivo(serie, max_p, max_q, max_d, max_P, max_Q, max_D, m, crit, trend, verbose):
    melhor = None
    melhor_val = float("inf")

    p_range = range(0, max_p + 1)
    d_range = range(0, max_d + 1)
    q_range = range(0, max_q + 1)
    P_range = range(0, max_P + 1) if m > 1 else [0]
    D_range = range(0, max_D + 1) if m > 1 else [0]
    Q_range = range(0, max_Q + 1) if m > 1 else [0]

    for p, d, q, P, D, Q in itertools.product(p_range, d_range, q_range, P_range, D_range, Q_range):
        if p + q == 0 and P + Q == 0:
            continue
        res = _tentar_modelo(serie, p, d, q, P, D, Q, m, trend)
        if res is None:
            continue
        val = _valor_criterio(res, crit)
        if verbose:
            print(f"  {res.modelo:40s}  {crit.upper()}={val:.4f}")
        if val < melhor_val:
            melhor_val = val
            melhor = res

    if melhor is None:
        raise RuntimeError("Nenhum modelo convergiu durante auto_arima")
    return melhor


def _auto_stepwise(serie, max_p, max_q, max_d, max_P, max_Q, max_D, m, crit, trend, verbose):
    """
    Busca stepwise inspirada no algoritmo Hyndman-Khandakar:
    1. Determina d (e D se m>1) pelos testes de raiz unitária simplificados
    2. Parte de ARIMA(2,d,2) e explora vizinhança variando p e q em ±1
    3. Termina quando nenhum vizinho melhora o critério
    """
    # Estimar d inicial pela variância das diferenças
    d = _estimar_d(serie, max_d)
    D = _estimar_D(serie, d, m, max_D) if m > 1 else 0

    # Ponto de partida
    candidatos_iniciais = [(2, d, 2, 0, D, 0), (1, d, 1, 0, D, 0), (0, d, 1, 0, D, 0), (1, d, 0, 0, D, 0)]
    melhor = None
    melhor_val = float("inf")

    for p, d_, q, P, D_, Q in candidatos_iniciais:
        res = _tentar_modelo(serie, p, d_, q, P, D_, Q, m, trend)
        if res is None:
            continue
        val = _valor_criterio(res, crit)
        if val < melhor_val:
            melhor_val = val
            melhor = res

    if melhor is None:
        return _auto_exaustivo(serie, max_p, max_q, max_d, max_P, max_Q, max_D, m, crit, trend, verbose)

    # Explorar vizinhança
    melhorou = True
    while melhorou:
        melhorou = False
        ordem_atual = melhor.ordem
        if len(ordem_atual) == 7:
            p0, d0, q0, P0, D0, Q0, _ = ordem_atual
        else:
            p0, d0, q0 = ordem_atual
            P0, D0, Q0 = 0, D, 0

        for dp, dq in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1)]:
            np_ = max(0, min(p0 + dp, max_p))
            nq  = max(0, min(q0 + dq, max_q))
            res = _tentar_modelo(serie, np_, d0, nq, P0, D0, Q0, m, trend)
            if res is None:
                continue
            val = _valor_criterio(res, crit)
            if verbose:
                print(f"  {res.modelo:40s}  {crit.upper()}={val:.4f}")
            if val < melhor_val - 1e-6:
                melhor_val = val
                melhor = res
                melhorou = True

    return melhor


def _estimar_d(serie: pd.Series, max_d: int) -> int:
    """Estima d pela variância mínima das diferenças sucessivas."""
    from statsmodels.tsa.stattools import adfuller

    s = serie.dropna()
    for d in range(max_d + 1):
        try:
            stat, pval, *_ = adfuller(s if d == 0 else s.diff(d).dropna(), autolag="AIC")
            if pval < 0.05:
                return d
        except Exception:
            pass
        if d < max_d:
            s = s.diff().dropna()
    return max_d


def _estimar_D(serie: pd.Series, d: int, m: int, max_D: int) -> int:
    """Estima D sazonal pela variância das diferenças sazonais."""
    s = serie.dropna()
    if d > 0:
        s = s.diff(d).dropna()
    var0 = s.var()
    var1 = s.diff(m).dropna().var() if len(s) > m else var0
    return 1 if (var1 < var0 and max_D >= 1) else 0


# ---------------------------------------------------------------------------
# criterios — tabela comparativa
# ---------------------------------------------------------------------------

def criterios(
    serie: pd.Series,
    ordens: List[Tuple[int, int]],
    *,
    d: int = 0,
    trend: str = "n",
) -> pd.DataFrame:
    """
    Compara múltiplas ordens ARMA e retorna tabela com critérios de informação.

    Parâmetros
    ----------
    serie  : pd.Series com índice datetime
    ordens : lista de tuplas (p, q)
    d      : grau de integração comum (padrão 0)
    trend  : 'n' | 'c' | 'ct'

    Retorna DataFrame indexado por (p, q) com colunas AIC, BIC, HQIC, LogLik, nobs
    """
    registros = []
    for (p, q) in ordens:
        res = None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = _arima(serie, p, d, q, trend=trend)
        except Exception:
            pass
        registros.append({
            "p": p,
            "q": q,
            "AIC":    res.aic if res else float("nan"),
            "BIC":    res.bic if res else float("nan"),
            "HQIC":   res.hqic if res else float("nan"),
            "LogLik": res.log_likelihood if res else float("nan"),
            "nobs":   res.nobs if res else float("nan"),
        })

    df = pd.DataFrame(registros).set_index(["p", "q"]).sort_values("AIC")
    return df


# ---------------------------------------------------------------------------
# acf_pacf — autocorrelação e autocorrelação parcial
# ---------------------------------------------------------------------------

def acf_pacf(
    serie: pd.Series,
    *,
    nlags: int = 40,
    alpha: float = 0.05,
) -> ACFResult:
    """
    Calcula ACF, PACF, intervalos de confiança e estatística Ljung-Box.

    Parâmetros
    ----------
    serie : pd.Series
    nlags : int — número de lags (padrão 40)
    alpha : float — nível do IC (padrão 0.05 → IC 95%)

    Retorna ACFResult
    """
    from statsmodels.tsa.stattools import acf, pacf, q_stat

    s = serie.dropna()
    nlags_eff = min(nlags, len(s) // 2 - 1)

    acf_vals, ic_acf = acf(s, nlags=nlags_eff, alpha=alpha, fft=True)
    pacf_vals, ic_pacf = pacf(s, nlags=nlags_eff, alpha=alpha, method="ywm")

    # Ljung-Box: q_stat recebe acf a partir do lag 1 (sem lag 0)
    qstat, qpval = q_stat(acf_vals[1:], nobs=len(s))
    lags_lb = np.arange(1, len(qstat) + 1)
    ljung = pd.DataFrame({
        "lag":    lags_lb,
        "Q":      qstat,
        "pvalue": qpval,
    }).set_index("lag")

    return ACFResult(
        acf=acf_vals,
        pacf=pacf_vals,
        ic_acf=ic_acf,
        ic_pacf=ic_pacf,
        nlags=nlags_eff,
        ljung_box=ljung,
    )
