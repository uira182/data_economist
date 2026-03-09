"""
Análise de correlação e covariância.

Funções:
    pearson()         — Correlação linear de Pearson
    spearman()        — Correlação de Spearman (por postos)
    kendall_b()       — Tau-b de Kendall
    kendall_a()       — Tau-a de Kendall
    parcial()         — Correlação parcial (controlando por outras variáveis)
    covariancia()     — Matriz de covariância
    matriz_correlacao() — Matriz de correlação com método escolhido
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from ._resultado import TesteResult, _concluir


@dataclass
class CorrelacaoResult:
    """
    Resultado de um teste de correlação entre duas séries.

    Atributos
    ---------
    coeficiente : float
        Coeficiente de correlação estimado.
    pvalue : float
        p-valor da hipótese H0: correlação = 0.
    metodo : str
        "pearson", "spearman", "kendall_b" ou "kendall_a".
    n : int
        Número de observações usadas (pares completos).
    intervalo_confianca : tuple ou None
        IC 95% para o coeficiente (Pearson usa transformação Fisher-Z).
    rejeita_h0 : bool
        True se H0: rho=0 é rejeitada ao nível alpha.
    alpha : float
    """

    coeficiente: float
    pvalue: float
    metodo: str
    n: int
    intervalo_confianca: Optional[tuple] = None
    rejeita_h0: bool = False
    alpha: float = 0.05

    def __str__(self) -> str:
        ic = (
            f"  IC 95%    : [{self.intervalo_confianca[0]:.4f}, {self.intervalo_confianca[1]:.4f}]"
            if self.intervalo_confianca
            else ""
        )
        linhas = [
            f"Correlação ({self.metodo})",
            f"  r         : {self.coeficiente:.4f}",
            f"  p-valor   : {self.pvalue:.4f}",
            f"  N         : {self.n}",
        ]
        if ic:
            linhas.append(ic)
        linhas.append(f"  Rejeita H0: {self.rejeita_h0} (alpha={self.alpha})")
        return "\n".join(linhas)


def _pares(x: pd.Series, y: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Remove NaN dos pares e retorna arrays alinhados."""
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df) < 3:
        raise ValueError("correlacao: precisa de ao menos 3 pares completos.")
    return df["x"].values, df["y"].values


def _ic_fisher(r: float, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Intervalo de confiança via transformação Fisher-Z."""
    from scipy import stats as sp
    if abs(r) >= 1.0:
        return (float(r), float(r))
    r_safe = float(np.clip(r, -0.9999999, 0.9999999))
    z = np.arctanh(r_safe)
    se = 1 / np.sqrt(max(n - 3, 1))
    z_crit = sp.norm.ppf(1 - alpha / 2)
    lo = float(np.clip(np.tanh(z - z_crit * se), -1.0, 1.0))
    hi = float(np.clip(np.tanh(z + z_crit * se), -1.0, 1.0))
    return (lo, hi)


# ---------------------------------------------------------------------------
# Pearson
# ---------------------------------------------------------------------------

def pearson(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> CorrelacaoResult:
    """
    Correlação linear de Pearson.

    r = cov(X,Y) / (std(X) * std(Y))

    Mede a relação linear entre duas variáveis. Sensível a outliers.
    Assume que ambas as variáveis seguem distribuição normal para
    inferência exata; para amostras grandes é assintoticamente válido.

    Parâmetros
    ----------
    x, y : pd.Series
        Séries numéricas. NaN nos pares são removidos.
    alpha : float
        Nível de significância para IC e conclusão.

    H0: rho = 0 (não há correlação linear).
    """
    from scipy import stats as sp

    xv, yv = _pares(x, y)
    r, pval = sp.pearsonr(xv, yv)
    n = len(xv)
    ic = _ic_fisher(float(r), n, alpha) if n >= 5 else None
    _, rejeita = _concluir(float(pval), alpha, "rho = 0")
    return CorrelacaoResult(
        coeficiente=float(r),
        pvalue=float(pval),
        metodo="pearson",
        n=n,
        intervalo_confianca=ic,
        rejeita_h0=rejeita,
        alpha=alpha,
    )


# ---------------------------------------------------------------------------
# Spearman
# ---------------------------------------------------------------------------

def spearman(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> CorrelacaoResult:
    """
    Correlação de Spearman (por postos).

    Pearson aplicado aos postos das variáveis. Não assume normalidade nem
    linearidade. Robusto a outliers e adequado para dados ordinais.

    rho_s = 1 - 6*sum(d_i²) / (n*(n²-1)),  onde d_i = posto(x_i) - posto(y_i)

    H0: rho_s = 0.
    """
    from scipy import stats as sp

    xv, yv = _pares(x, y)
    r, pval = sp.spearmanr(xv, yv)
    n = len(xv)
    ic = _ic_fisher(float(r), n, alpha) if n >= 5 else None
    _, rejeita = _concluir(float(pval), alpha, "rho_s = 0")
    return CorrelacaoResult(
        coeficiente=float(r),
        pvalue=float(pval),
        metodo="spearman",
        n=n,
        intervalo_confianca=ic,
        rejeita_h0=rejeita,
        alpha=alpha,
    )


# ---------------------------------------------------------------------------
# Kendall tau-b
# ---------------------------------------------------------------------------

def kendall_b(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> CorrelacaoResult:
    """
    Tau-b de Kendall.

    Mede concordância de pares: tau_b = (C - D) / sqrt((C+D+T_x)*(C+D+T_y))
    onde C = concordantes, D = discordantes, T_x/T_y = empates em x/y.
    Corrige para empates; adequado para escala ordinal.

    H0: tau_b = 0.
    """
    from scipy import stats as sp

    xv, yv = _pares(x, y)
    tau, pval = sp.kendalltau(xv, yv, variant="b")
    n = len(xv)
    _, rejeita = _concluir(float(pval), alpha, "tau_b = 0")
    return CorrelacaoResult(
        coeficiente=float(tau),
        pvalue=float(pval),
        metodo="kendall_b",
        n=n,
        rejeita_h0=rejeita,
        alpha=alpha,
    )


# ---------------------------------------------------------------------------
# Kendall tau-a
# ---------------------------------------------------------------------------

def kendall_a(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> CorrelacaoResult:
    """
    Tau-a de Kendall.

    tau_a = (C - D) / (n*(n-1)/2)
    Não corrige para empates. Mais conservador que tau-b.

    H0: tau_a = 0 (mesma distribuição dos p-valores que tau-b).
    """
    from scipy import stats as sp

    xv, yv = _pares(x, y)
    n = len(xv)

    # Cálculo manual do tau-a
    c, d = 0, 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = xv[i] - xv[j]
            dy = yv[i] - yv[j]
            if dx * dy > 0:
                c += 1
            elif dx * dy < 0:
                d += 1
    total_pares = n * (n - 1) / 2
    tau_a = (c - d) / total_pares if total_pares > 0 else 0.0

    # p-valor aproximado (normal para n > 10)
    if n > 10:
        var = (2 * (2 * n + 5)) / (9 * n * (n - 1))
        z = tau_a / np.sqrt(var)
        pval = float(2 * sp.norm.sf(abs(z)))
    else:
        # Para amostras pequenas, usa p-valor do tau-b como aproximação
        _, pval = sp.kendalltau(xv, yv, variant="b")
        pval = float(pval)

    _, rejeita = _concluir(pval, alpha, "tau_a = 0")
    return CorrelacaoResult(
        coeficiente=float(tau_a),
        pvalue=pval,
        metodo="kendall_a",
        n=n,
        rejeita_h0=rejeita,
        alpha=alpha,
    )


# ---------------------------------------------------------------------------
# Correlação parcial
# ---------------------------------------------------------------------------

def parcial(
    df: pd.DataFrame,
    x: str,
    y: str,
    controles: list[str],
    alpha: float = 0.05,
) -> CorrelacaoResult:
    """
    Correlação parcial entre x e y, controlando por variáveis de controle.

    Método dos resíduos: regride x e y nas variáveis de controle,
    obtém os resíduos e calcula a correlação de Pearson entre eles.
    Mede a associação linear entre x e y removendo a influência comum
    das variáveis de controle.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com todas as colunas.
    x : str
        Nome da primeira variável.
    y : str
        Nome da segunda variável.
    controles : list[str]
        Nomes das variáveis de controle.
    alpha : float

    H0: correlação parcial = 0.
    """
    from scipy import stats as sp

    colunas = [x, y] + list(controles)
    sub = df[colunas].dropna()
    if len(sub) < len(colunas) + 2:
        raise ValueError("parcial(): observações insuficientes após remover NaN.")

    X_ctrl = sub[controles].values
    # Adicionar intercepto
    X_ctrl = np.column_stack([np.ones(len(X_ctrl)), X_ctrl])

    def residuos(v: np.ndarray) -> np.ndarray:
        beta, *_ = np.linalg.lstsq(X_ctrl, v, rcond=None)
        return v - X_ctrl @ beta

    rx = residuos(sub[x].values)
    ry = residuos(sub[y].values)

    r, pval = sp.pearsonr(rx, ry)
    n = len(rx)
    ic = _ic_fisher(float(r), n, alpha) if n >= 5 else None
    _, rejeita = _concluir(float(pval), alpha, "correlação parcial = 0")
    return CorrelacaoResult(
        coeficiente=float(r),
        pvalue=float(pval),
        metodo=f"parcial (controles: {controles})",
        n=n,
        intervalo_confianca=ic,
        rejeita_h0=rejeita,
        alpha=alpha,
    )


# ---------------------------------------------------------------------------
# Covariância e matriz de correlação
# ---------------------------------------------------------------------------

def covariancia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Matriz de covariância amostral do DataFrame.

    Usa ddof=1 (estimativa não viesada). Linhas/colunas com NaN são tratadas
    pairwise (cov calculado apenas com pares completos).

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com colunas numéricas.

    Retorna
    -------
    pd.DataFrame
        Matriz de covariância (n_vars x n_vars).
    """
    num = df.select_dtypes(include="number")
    if num.shape[1] < 2:
        raise ValueError("covariancia(): precisa de ao menos 2 colunas numéricas.")
    return num.cov(min_periods=3)


def matriz_correlacao(
    df: pd.DataFrame,
    metodo: str = "pearson",
) -> pd.DataFrame:
    """
    Matriz de correlação entre todas as colunas numéricas do DataFrame.

    Parâmetros
    ----------
    df : pd.DataFrame
    metodo : str
        "pearson" (padrão), "spearman" ou "kendall".

    Retorna
    -------
    pd.DataFrame
        Matriz de correlação (n_vars x n_vars), valores entre -1 e 1.
    """
    if metodo not in ("pearson", "spearman", "kendall"):
        raise ValueError(
            f"matriz_correlacao(): metodo '{metodo}' inválido. "
            "Use 'pearson', 'spearman' ou 'kendall'."
        )
    num = df.select_dtypes(include="number")
    if num.shape[1] < 2:
        raise ValueError("matriz_correlacao(): precisa de ao menos 2 colunas numéricas.")
    return num.corr(method=metodo)
