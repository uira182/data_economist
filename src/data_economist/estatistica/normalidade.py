"""
Testes de normalidade e aderência a distribuições (EDF — Empirical Distribution Function).

Funções disponíveis:
    ks()               — Kolmogorov-Smirnov
    lilliefors()       — Lilliefors (KS com parâmetros estimados)
    anderson_darling() — Anderson-Darling
    cramer_von_mises() — Cramer-von Mises
    watson()           — Watson (variante circular do Cramer-von Mises)

Todos retornam TesteResult. H0 em todos: a amostra segue a distribuição especificada.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._resultado import TesteResult, _concluir


def _validar(serie: pd.Series, nome: str) -> np.ndarray:
    if not pd.api.types.is_numeric_dtype(serie):
        raise ValueError(f"{nome}(): a série deve ser numérica.")
    s = serie.dropna().values
    if len(s) < 5:
        raise ValueError(f"{nome}(): precisa de ao menos 5 observações.")
    return s


# ---------------------------------------------------------------------------
# Kolmogorov-Smirnov
# ---------------------------------------------------------------------------

def ks(
    serie: pd.Series,
    distribuicao: str = "normal",
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste de Kolmogorov-Smirnov (KS) de aderência.

    Compara a função de distribuição empírica (EDF) com uma distribuição teórica.
    Estatística: D = max|F_n(x) - F(x)|, onde F_n é a EDF e F é a CDF teórica.

    Quando distribuicao="normal", usa média e desvio padrão amostrais (equivale
    ao Lilliefors para normalidade). Para uma comparação mais rigorosa com
    parâmetros desconhecidos, prefira lilliefors().

    Parâmetros
    ----------
    serie : pd.Series
        Série numérica.
    distribuicao : str
        "normal" (padrão), "exponencial", "logistica", "uniform".
    alpha : float
        Nível de significância (padrão 0.05).

    H0: a amostra segue a distribuição especificada.
    """
    from scipy import stats as sp

    s = _validar(serie, "ks")
    _mapa = {
        "normal": ("norm", (s.mean(), s.std(ddof=1))),
        "exponencial": ("expon", (s.min(), s.mean() - s.min())),
        "logistica": ("logistic", (s.mean(), s.std(ddof=1) * np.sqrt(3) / np.pi)),
        "uniform": ("uniform", (s.min(), s.max() - s.min())),
    }
    dist_key = distribuicao.lower()
    if dist_key not in _mapa:
        raise ValueError(
            f"ks(): distribuição '{distribuicao}' inválida. "
            f"Use: {list(_mapa.keys())}"
        )
    scipy_name, args = _mapa[dist_key]
    stat, pval = sp.kstest(s, scipy_name, args=args)
    h0 = f"a amostra segue distribuição {distribuicao}"
    conclusao, rejeita = _concluir(pval, alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Kolmogorov-Smirnov",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n": len(s), "distribuicao": distribuicao},
    )


# ---------------------------------------------------------------------------
# Lilliefors
# ---------------------------------------------------------------------------

def lilliefors(
    serie: pd.Series,
    distribuicao: str = "normal",
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste de Lilliefors — KS com correção para parâmetros estimados.

    Mais adequado que o KS simples para testar normalidade quando a média
    e o desvio padrão não são conhecidos a priori (caso mais comum).
    Usa a distribuição de referência de Lilliefors (1967) para os valores
    críticos, obtida por simulação.

    Parâmetros
    ----------
    serie : pd.Series
    distribuicao : str
        "normal" ou "exponencial".
    alpha : float

    H0: a amostra segue a distribuição (com parâmetros não especificados).
    """
    from statsmodels.stats.diagnostic import lilliefors as sm_lilliefors

    s = _validar(serie, "lilliefors")
    dist_key = distribuicao.lower()
    if dist_key not in ("normal", "exponencial", "expon"):
        raise ValueError("lilliefors(): distribuição deve ser 'normal' ou 'exponencial'.")
    sm_dist = "norm" if dist_key == "normal" else "exp"
    stat, pval = sm_lilliefors(s, dist=sm_dist)
    h0 = f"a amostra segue distribuição {distribuicao} (parâmetros estimados)"
    conclusao, rejeita = _concluir(pval, alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Lilliefors",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n": len(s), "distribuicao": distribuicao},
    )


# ---------------------------------------------------------------------------
# Anderson-Darling
# ---------------------------------------------------------------------------

def anderson_darling(
    serie: pd.Series,
    distribuicao: str = "normal",
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste de Anderson-Darling.

    Versão ponderada do Cramer-von Mises que dá mais peso às caudas da
    distribuição. Mais poderoso que o KS para detectar desvios nas caudas.
    Estatística: A² = -n - (1/n) * sum((2i-1)*[ln F(x_i) + ln(1-F(x_{n+1-i}))])

    Distribuições suportadas pelo scipy: normal, exponencial, logistic,
    gumbel, extreme1, weibull_min.

    Parâmetros
    ----------
    serie : pd.Series
    distribuicao : str
        "normal" (padrão), "exponencial", "logistica", "gumbel", "extreme_value",
        "weibull".
    alpha : float

    H0: a amostra segue a distribuição especificada.
    """
    from scipy import stats as sp

    s = _validar(serie, "anderson_darling")
    _mapa_scipy = {
        "normal": "norm",
        "exponencial": "expon",
        "logistica": "logistic",
        "gumbel": "gumbel",
        "extreme_value": "extreme1",
        "weibull": "weibull_min",
    }
    dist_key = distribuicao.lower()
    if dist_key not in _mapa_scipy:
        raise ValueError(
            f"anderson_darling(): distribuição '{distribuicao}' inválida. "
            f"Use: {list(_mapa_scipy.keys())}"
        )
    scipy_dist = _mapa_scipy[dist_key]
    critico_5pct = float("nan")
    # Tenta usar method="interpolate" disponível a partir do scipy 1.17
    try:
        resultado = sp.anderson(s, dist=scipy_dist, method="interpolate")
        stat = float(resultado.statistic)
        pval = float(resultado.pvalue)
    except TypeError:
        # Fallback para versões anteriores ao 1.17
        resultado = sp.anderson(s, dist=scipy_dist)  # type: ignore[call-arg]
        stat = float(resultado.statistic)
        niveis = resultado.significance_level / 100.0
        criticos = resultado.critical_values
        critico_5pct = float(criticos[2]) if len(criticos) > 2 else float("nan")
        if stat <= criticos[0]:
            pval = float(niveis[0])
        elif stat >= criticos[-1]:
            pval = float(niveis[-1])
        else:
            pval = float(np.interp(stat, criticos, niveis))

    h0 = f"a amostra segue distribuição {distribuicao}"
    conclusao, rejeita = _concluir(pval, alpha, h0)
    return TesteResult(
        statistic=stat,
        pvalue=pval,
        metodo="Anderson-Darling",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={
            "n": len(s),
            "distribuicao": distribuicao,
            "critico_5pct": critico_5pct,
        },
    )


# ---------------------------------------------------------------------------
# Cramer-von Mises
# ---------------------------------------------------------------------------

def cramer_von_mises(
    serie: pd.Series,
    distribuicao: str = "normal",
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste de Cramer-von Mises.

    Mede a distância quadrática integrada entre a EDF e a CDF teórica:
    C = (1/12n) + sum((F(x_i) - (2i-1)/(2n))²)

    Parâmetros
    ----------
    serie : pd.Series
    distribuicao : str
        "normal" (padrão), "exponencial", "logistica", "uniform".
    alpha : float

    H0: a amostra segue a distribuição especificada.
    """
    from scipy import stats as sp

    s = _validar(serie, "cramer_von_mises")
    _mapa = {
        "normal": ("norm", {}),
        "exponencial": ("expon", {}),
        "logistica": ("logistic", {}),
        "uniform": ("uniform", {}),
    }
    dist_key = distribuicao.lower()
    if dist_key not in _mapa:
        raise ValueError(
            f"cramer_von_mises(): distribuição '{distribuicao}' inválida. "
            f"Use: {list(_mapa.keys())}"
        )
    scipy_name, _ = _mapa[dist_key]
    dist_obj = getattr(sp, scipy_name)
    params = dist_obj.fit(s)
    resultado = sp.cramervonmises(s, scipy_name, args=params)
    stat = float(resultado.statistic)
    pval = float(resultado.pvalue)
    h0 = f"a amostra segue distribuição {distribuicao}"
    conclusao, rejeita = _concluir(pval, alpha, h0)
    return TesteResult(
        statistic=stat,
        pvalue=pval,
        metodo="Cramer-von Mises",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n": len(s), "distribuicao": distribuicao},
    )


# ---------------------------------------------------------------------------
# Watson
# ---------------------------------------------------------------------------

def watson(
    serie: pd.Series,
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste de Watson (variante do Cramer-von Mises para dados circulares).

    A estatística de Watson corrige o Cramer-von Mises pelo desvio da
    média empírica em relação à média teórica:
    U² = C - n*(mean(F(x_i)) - 0.5)²

    Para dados não circulares, funciona como teste de uniformidade sobre
    F(x_i), tornando-o invariante a transformações de localização.

    Parâmetros
    ----------
    serie : pd.Series
        Série numérica. Testa normalidade (transforma para U(0,1) via CDF normal).
    alpha : float

    H0: a amostra segue distribuição normal.
    """
    from scipy import stats as sp

    s = _validar(serie, "watson")
    n = len(s)
    s_sorted = np.sort(s)

    # Transformar para U(0,1) via CDF normal com parâmetros estimados
    mu, sigma = s_sorted.mean(), s_sorted.std(ddof=1)
    u = sp.norm.cdf(s_sorted, loc=mu, scale=sigma)

    # Cramer-von Mises: C = sum((u_i - (2i-1)/(2n))²) + 1/(12n)
    i = np.arange(1, n + 1)
    c = np.sum((u - (2 * i - 1) / (2 * n)) ** 2) + 1 / (12 * n)

    # Watson: U² = C - n*(mean(u) - 0.5)²
    u2 = c - n * (u.mean() - 0.5) ** 2
    stat = float(u2)

    # Valores críticos de Watson (1961): rejeita H0 se U² > valor crítico.
    # Mapeamento: crit ascendente → alpha descendente
    # stat < 0.152 → p-valor > 0.10 (não rejeita)
    # stat > 0.268 → p-valor < 0.01 (rejeita fortemente)
    crits_asc = [0.152, 0.187, 0.221, 0.268]   # críticos em ordem crescente
    alphas_desc = [0.10, 0.05, 0.025, 0.01]     # alpha correspondente (decrescente)
    if stat < crits_asc[0]:
        pval = 0.10  # p-valor conservador >= 0.10
    elif stat > crits_asc[-1]:
        pval = 0.005
    else:
        pval = float(np.interp(stat, crits_asc, alphas_desc))

    h0 = "a amostra segue distribuição normal"
    conclusao, rejeita = _concluir(pval, alpha, h0)
    return TesteResult(
        statistic=stat,
        pvalue=pval,
        metodo="Watson",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n": n, "nota": "p-valor aproximado por interpolação nos valores críticos tabelados"},
    )
