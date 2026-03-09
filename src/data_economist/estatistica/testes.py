"""
Testes de hipótese paramétricos e não paramétricos.

Funções:
    ttest()          — t-test (uma amostra, duas independentes, pareado)
    anova()          — ANOVA de um fator (F de Fisher)
    wilcoxon()       — Postos sinalizados de Wilcoxon
    mann_whitney()   — U de Mann-Whitney
    kruskal_wallis() — Kruskal-Wallis (ANOVA não paramétrico)
    van_der_waerden()— Scores normais de van der Waerden
    teste_f()        — Teste F para igualdade de variâncias
    bartlett()       — Bartlett (homogeneidade de variâncias)
    levene()         — Levene (homogeneidade de variâncias, robusto)
    brown_forsythe() — Brown-Forsythe (Levene com mediana)
    siegel_tukey()   — Siegel-Tukey (dispersões)
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from ._resultado import TesteResult, _concluir


def _arr(serie: pd.Series, nome: str) -> np.ndarray:
    if not pd.api.types.is_numeric_dtype(serie):
        raise ValueError(f"{nome}(): a série deve ser numérica.")
    s = serie.dropna().values
    if len(s) < 3:
        raise ValueError(f"{nome}(): precisa de ao menos 3 observações.")
    return s


def _grupos(*series, nome: str) -> list[np.ndarray]:
    gs = [_arr(pd.Series(s) if not isinstance(s, pd.Series) else s, nome) for s in series]
    if len(gs) < 2:
        raise ValueError(f"{nome}(): precisa de ao menos 2 grupos.")
    return gs


# ---------------------------------------------------------------------------
# t-test
# ---------------------------------------------------------------------------

def ttest(
    x: pd.Series,
    y: Optional[pd.Series] = None,
    valor_ref: float = 0.0,
    pareado: bool = False,
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste t de Student.

    Uma amostra: testa se a média de x é igual a valor_ref.
        t = (mean(x) - mu0) / (std(x) / sqrt(n))
        Graus de liberdade: n - 1.

    Duas amostras independentes: testa se mean(x) = mean(y).
        t = (mean(x) - mean(y)) / sqrt(var(x)/n1 + var(y)/n2)
        Graus de liberdade de Welch (não assume variâncias iguais).

    Duas amostras pareadas: testa se mean(x - y) = 0.
        t = mean(d) / (std(d) / sqrt(n)), d = x - y.

    Parâmetros
    ----------
    x : pd.Series
    y : pd.Series, opcional
        Se None: teste de uma amostra. Se fornecida: duas amostras.
    valor_ref : float
        Valor de referência para teste de uma amostra (padrão 0).
    pareado : bool
        Se True e y fornecido: teste pareado.
    alpha : float

    H0: média(x) = valor_ref  ou  média(x) = média(y).
    """
    from scipy import stats as sp

    xv = _arr(x, "ttest")
    if y is None:
        stat, pval = sp.ttest_1samp(xv, valor_ref)
        h0 = f"média(x) = {valor_ref}"
        metodo = "t-test (uma amostra)"
        extra = {"n": len(xv), "media_x": float(xv.mean()), "valor_ref": valor_ref}
    else:
        yv = _arr(y, "ttest")
        if pareado:
            stat, pval = sp.ttest_rel(xv, yv)
            h0 = "média(x - y) = 0"
            metodo = "t-test (pareado)"
            extra = {"n": min(len(xv), len(yv))}
        else:
            stat, pval = sp.ttest_ind(xv, yv, equal_var=False)
            h0 = "média(x) = média(y)"
            metodo = "t-test (duas amostras, Welch)"
            extra = {
                "n_x": len(xv),
                "n_y": len(yv),
                "media_x": float(xv.mean()),
                "media_y": float(yv.mean()),
            }
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo=metodo,
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params=extra,
    )


# ---------------------------------------------------------------------------
# ANOVA
# ---------------------------------------------------------------------------

def anova(*grupos: pd.Series, alpha: float = 0.05) -> TesteResult:
    """
    ANOVA de um fator (F de Fisher).

    F = (SQ_entre / gl_entre) / (SQ_dentro / gl_dentro)
    SQ_entre = sum(n_i * (mean_i - mean_total)²)
    SQ_dentro = sum(sum((x_ij - mean_i)²))

    Assume normalidade e homogeneidade de variâncias dentro dos grupos.
    Para violação de normalidade, use kruskal_wallis().

    Parâmetros
    ----------
    *grupos : pd.Series
        Dois ou mais grupos. NaN removidos por grupo.
    alpha : float

    H0: médias de todos os grupos são iguais.
    """
    from scipy import stats as sp

    gs = _grupos(*grupos, nome="anova")
    stat, pval = sp.f_oneway(*gs)
    h0 = "médias de todos os grupos são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="ANOVA (F de Fisher)",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_grupos": len(gs), "ns": [len(g) for g in gs]},
    )


# ---------------------------------------------------------------------------
# Wilcoxon
# ---------------------------------------------------------------------------

def wilcoxon(
    x: pd.Series,
    y: Optional[pd.Series] = None,
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste de postos sinalizados de Wilcoxon.

    Uma amostra: testa se a mediana de x é 0.
        Ordena |x_i| e soma os postos com sinal positivo/negativo.

    Duas amostras pareadas: testa se mediana(x - y) = 0.

    Alternativa não paramétrica ao t-test pareado.

    Parâmetros
    ----------
    x : pd.Series
    y : pd.Series, opcional
        Se fornecida: teste nas diferenças x - y.
    alpha : float

    H0: mediana = 0 (ou mediana das diferenças = 0).
    """
    from scipy import stats as sp

    xv = _arr(x, "wilcoxon")
    if y is not None:
        yv = _arr(y, "wilcoxon")
        n = min(len(xv), len(yv))
        diff = xv[:n] - yv[:n]
        stat, pval = sp.wilcoxon(diff)
        h0 = "mediana(x - y) = 0"
        metodo = "Wilcoxon (postos sinalizados, duas amostras)"
        extra = {"n": n}
    else:
        stat, pval = sp.wilcoxon(xv)
        h0 = "mediana(x) = 0"
        metodo = "Wilcoxon (postos sinalizados, uma amostra)"
        extra = {"n": len(xv)}
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo=metodo,
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params=extra,
    )


# ---------------------------------------------------------------------------
# Mann-Whitney U
# ---------------------------------------------------------------------------

def mann_whitney(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste U de Mann-Whitney (Wilcoxon de soma de postos).

    U = número de pares (x_i, y_j) onde x_i > y_j.
    Equivalente ao teste de Wilcoxon de soma de postos para duas amostras
    independentes. Não assume normalidade.

    H0: as distribuições de x e y são iguais (P(x > y) = 0.5).
    """
    from scipy import stats as sp

    xv = _arr(x, "mann_whitney")
    yv = _arr(y, "mann_whitney")
    stat, pval = sp.mannwhitneyu(xv, yv, alternative="two-sided")
    h0 = "distribuições de x e y são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Mann-Whitney U",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_x": len(xv), "n_y": len(yv)},
    )


# ---------------------------------------------------------------------------
# Kruskal-Wallis
# ---------------------------------------------------------------------------

def kruskal_wallis(*grupos: pd.Series, alpha: float = 0.05) -> TesteResult:
    """
    Teste de Kruskal-Wallis.

    Versão não paramétrica do ANOVA de um fator. Usa os postos globais
    ao invés dos valores originais.
    H = (12 / (N*(N+1))) * sum(R_i²/n_i) - 3*(N+1)
    Sob H0, H ~ chi²(k-1).

    H0: medianas de todos os grupos são iguais.
    """
    from scipy import stats as sp

    gs = _grupos(*grupos, nome="kruskal_wallis")
    stat, pval = sp.kruskal(*gs)
    h0 = "medianas de todos os grupos são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Kruskal-Wallis",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_grupos": len(gs), "gl": len(gs) - 1},
    )


# ---------------------------------------------------------------------------
# van der Waerden
# ---------------------------------------------------------------------------

def van_der_waerden(*grupos: pd.Series, alpha: float = 0.05) -> TesteResult:
    """
    Teste de scores normais de van der Waerden.

    Converte postos em scores normais: a_i = Phi^{-1}(rank_i / (N+1))
    Calcula o F de ANOVA nesses scores.
    Mais poderoso que Kruskal-Wallis quando os dados são próximos da normal,
    mais robusto que ANOVA quando há desvios moderados.

    H0: populações têm a mesma distribuição.
    """
    from scipy import stats as sp

    gs = _grupos(*grupos, nome="van_der_waerden")
    todos = np.concatenate(gs)
    n_total = len(todos)

    # Postos globais (1 a N)
    ranks = sp.rankdata(todos)
    scores = sp.norm.ppf(ranks / (n_total + 1))

    # Separar scores por grupo
    idx = 0
    scores_grupos = []
    for g in gs:
        scores_grupos.append(scores[idx: idx + len(g)])
        idx += len(g)

    # F de ANOVA nos scores
    stat, pval = sp.f_oneway(*scores_grupos)
    h0 = "populações têm a mesma distribuição"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="van der Waerden (scores normais)",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_grupos": len(gs), "n_total": n_total},
    )


# ---------------------------------------------------------------------------
# Teste F para variâncias
# ---------------------------------------------------------------------------

def teste_f(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste F para igualdade de variâncias entre dois grupos.

    F = var(x) / var(y), com graus de liberdade (n1-1, n2-1).
    Assume normalidade. Para alternativa robusta, use levene() ou brown_forsythe().

    H0: var(x) = var(y).
    """
    from scipy import stats as sp

    xv = _arr(x, "teste_f")
    yv = _arr(y, "teste_f")
    vx = float(np.var(xv, ddof=1))
    vy = float(np.var(yv, ddof=1))
    stat = vx / vy if vy > 0 else float("inf")
    df1 = len(xv) - 1
    df2 = len(yv) - 1
    # p-valor bilateral
    pval = 2 * min(
        float(sp.f.cdf(stat, df1, df2)),
        float(sp.f.sf(stat, df1, df2)),
    )
    h0 = "var(x) = var(y)"
    conclusao, rejeita = _concluir(pval, alpha, h0)
    return TesteResult(
        statistic=stat,
        pvalue=pval,
        metodo="Teste F (variâncias)",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"df1": df1, "df2": df2, "var_x": vx, "var_y": vy},
    )


# ---------------------------------------------------------------------------
# Bartlett
# ---------------------------------------------------------------------------

def bartlett(*grupos: pd.Series, alpha: float = 0.05) -> TesteResult:
    """
    Teste de Bartlett para homogeneidade de variâncias.

    Assume normalidade dos grupos. Mais sensível a desvios de normalidade
    do que o Levene. Adequado quando os grupos têm distribuição normal.

    H0: variâncias de todos os grupos são iguais.
    """
    from scipy import stats as sp

    gs = _grupos(*grupos, nome="bartlett")
    stat, pval = sp.bartlett(*gs)
    h0 = "variâncias de todos os grupos são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Bartlett",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_grupos": len(gs)},
    )


# ---------------------------------------------------------------------------
# Levene
# ---------------------------------------------------------------------------

def levene(*grupos: pd.Series, alpha: float = 0.05) -> TesteResult:
    """
    Teste de Levene para homogeneidade de variâncias.

    Baseado nos desvios em relação à média do grupo: |x_ij - mean_i|.
    Robusto a desvios de normalidade. ANOVA aplicado nesses desvios.

    H0: variâncias de todos os grupos são iguais.
    """
    from scipy import stats as sp

    gs = _grupos(*grupos, nome="levene")
    stat, pval = sp.levene(*gs, center="mean")
    h0 = "variâncias de todos os grupos são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Levene",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_grupos": len(gs)},
    )


# ---------------------------------------------------------------------------
# Brown-Forsythe
# ---------------------------------------------------------------------------

def brown_forsythe(*grupos: pd.Series, alpha: float = 0.05) -> TesteResult:
    """
    Teste de Brown-Forsythe para homogeneidade de variâncias.

    Variante do Levene que usa a mediana em vez da média do grupo:
    |x_ij - median_i|. Mais robusto que o Levene para distribuições
    assimétricas.

    H0: variâncias de todos os grupos são iguais.
    """
    from scipy import stats as sp

    gs = _grupos(*grupos, nome="brown_forsythe")
    stat, pval = sp.levene(*gs, center="median")
    h0 = "variâncias de todos os grupos são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Brown-Forsythe",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_grupos": len(gs)},
    )


# ---------------------------------------------------------------------------
# Siegel-Tukey
# ---------------------------------------------------------------------------

def siegel_tukey(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> TesteResult:
    """
    Teste de Siegel-Tukey para diferença de dispersão.

    Atribui ranks alternados ao conjunto combinado ordenado:
    1, 4, 3, 2, 5, 8, 7, 6, 9, 12, ...
    (começa nos extremos e alterna para dentro). Aplica Mann-Whitney
    nesses ranks para testar se as dispersões são iguais.

    H0: as dispersões de x e y são iguais.
    """
    from scipy import stats as sp

    xv = _arr(x, "siegel_tukey")
    yv = _arr(y, "siegel_tukey")
    n = len(xv) + len(yv)

    # Ordenar conjunto combinado mantendo rótulo de grupo
    combinado = np.concatenate([xv, yv])
    labels = np.array([0] * len(xv) + [1] * len(yv))
    ordem = np.argsort(combinado, kind="stable")
    labels_ord = labels[ordem]

    # Ranks de Siegel-Tukey: alterna dos extremos para o centro
    ranks = np.zeros(n)
    esq, dir_ = 0, n - 1
    r = 1
    while esq <= dir_:
        ranks[esq] = r
        r += 1
        if esq != dir_:
            ranks[dir_] = r
            r += 1
        esq += 1
        dir_ -= 1
        if esq <= dir_:
            ranks[dir_] = r
            r += 1
            if esq != dir_:
                ranks[esq] = r
                r += 1
            esq += 1
            dir_ -= 1

    ranks_x = ranks[labels_ord == 0]
    ranks_y = ranks[labels_ord == 1]
    stat, pval = sp.mannwhitneyu(ranks_x, ranks_y, alternative="two-sided")
    h0 = "dispersões de x e y são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Siegel-Tukey",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_x": len(xv), "n_y": len(yv)},
    )


# ---------------------------------------------------------------------------
# Mediana Chi-quadrado
# ---------------------------------------------------------------------------

def mediana_chi2(*grupos: pd.Series, alpha: float = 0.05) -> TesteResult:
    """
    Teste da mediana (Chi-quadrado).

    Calcula a mediana global e conta quantas observações de cada grupo
    estão acima e abaixo dela. Aplica qui-quadrado na tabela de contingência.

    H0: medianas de todos os grupos são iguais.
    """
    from scipy import stats as sp

    gs = _grupos(*grupos, nome="mediana_chi2")
    todos = np.concatenate(gs)
    mediana_global = float(np.median(todos))

    tabela = []
    for g in gs:
        acima = int(np.sum(g > mediana_global))
        abaixo = int(np.sum(g <= mediana_global))
        tabela.append([acima, abaixo])

    tabela_arr = np.array(tabela)
    stat, pval, gl, _ = sp.chi2_contingency(tabela_arr, correction=False)
    h0 = "medianas de todos os grupos são iguais"
    conclusao, rejeita = _concluir(float(pval), alpha, h0)
    return TesteResult(
        statistic=float(stat),
        pvalue=float(pval),
        metodo="Mediana Chi-quadrado",
        hipotese_nula=h0,
        conclusao=conclusao,
        rejeita_h0=rejeita,
        alpha=alpha,
        params={"n_grupos": len(gs), "mediana_global": mediana_global, "gl": int(gl)},
    )
