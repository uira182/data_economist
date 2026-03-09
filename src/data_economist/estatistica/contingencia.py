"""
Tabulação e análise de contingência.

Funções:
    tabular()  — Frequências absolutas e relativas de uma série
    cruzar()   — Tabela de contingência com medidas de associação e testes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from ._resultado import TesteResult, _concluir


@dataclass
class TabulacaoResult:
    """
    Resultado da tabulação univariada.

    Atributos
    ---------
    tabela : pd.DataFrame
        DataFrame com colunas: valor, freq_absoluta, freq_relativa, freq_acumulada.
    n : int
        Total de observações válidas.
    n_categorias : int
        Número de categorias distintas.
    nome : str
        Nome da série.
    """

    tabela: pd.DataFrame
    n: int
    n_categorias: int
    nome: str = ""

    def __str__(self) -> str:
        linhas = [
            f"Tabulação: {self.nome}" if self.nome else "Tabulação univariada",
            f"  N total     : {self.n}",
            f"  Categorias  : {self.n_categorias}",
            "",
            self.tabela.to_string(index=False),
        ]
        return "\n".join(linhas)


@dataclass
class ContingenciaResult:
    """
    Resultado da tabela de contingência cruzada.

    Atributos
    ---------
    tabela : pd.DataFrame
        Tabela de contingência (frequências observadas).
    tabela_esperada : pd.DataFrame
        Frequências esperadas sob independência.
    n : int
        Total de observações.
    chi2 : float
        Estatística qui-quadrado de Pearson: sum((O-E)²/E).
    chi2_pvalue : float
        p-valor do qui-quadrado.
    g2 : float
        Razão de verossimilhança G²: 2*sum(O*ln(O/E)).
    g2_pvalue : float
        p-valor do G².
    gl : int
        Graus de liberdade: (linhas-1)*(colunas-1).
    phi : float ou None
        Phi = sqrt(chi2/n). Válido apenas para tabelas 2x2.
    v_cramer : float
        V de Cramér = sqrt(chi2 / (n*(k-1))), k = min(linhas, colunas).
        Varia de 0 (independência) a 1 (associação perfeita).
    coef_contingencia : float
        Coeficiente de Contingência de Pearson = sqrt(chi2 / (chi2 + n)).
        Limitado superiormente por sqrt((k-1)/k).
    rejeita_independencia : bool
        True se qui-quadrado rejeita H0: independência ao nível alpha.
    alpha : float
    """

    tabela: pd.DataFrame
    tabela_esperada: pd.DataFrame
    n: int
    chi2: float
    chi2_pvalue: float
    g2: float
    g2_pvalue: float
    gl: int
    phi: Optional[float]
    v_cramer: float
    coef_contingencia: float
    rejeita_independencia: bool
    alpha: float = 0.05

    def __str__(self) -> str:
        linhas = [
            "Tabela de contingência",
            f"  N                  : {self.n}",
            f"  Chi² (Pearson)     : {self.chi2:.4f}  (p={self.chi2_pvalue:.4f})",
            f"  G² (Verossimilhança): {self.g2:.4f}  (p={self.g2_pvalue:.4f})",
            f"  Graus de liberdade : {self.gl}",
            f"  V de Cramér        : {self.v_cramer:.4f}",
            f"  Coef. Contingência : {self.coef_contingencia:.4f}",
        ]
        if self.phi is not None:
            linhas.append(f"  Phi (2x2)          : {self.phi:.4f}")
        linhas.append(
            f"  Rejeita independência: {self.rejeita_independencia} (alpha={self.alpha})"
        )
        return "\n".join(linhas)


# ---------------------------------------------------------------------------
# tabular()
# ---------------------------------------------------------------------------

def tabular(serie: pd.Series, alpha: float = 0.05) -> TabulacaoResult:
    """
    Tabulação univariada: frequências absolutas e relativas.

    Parâmetros
    ----------
    serie : pd.Series
        Série categórica, ordinal ou discreta. NaN são excluídos.
    alpha : float
        Não usado diretamente; reservado para extensões futuras.

    Retorna
    -------
    TabulacaoResult
        .tabela com colunas: valor, freq_absoluta, freq_relativa (%), freq_acumulada (%).

    Exemplo
    -------
    >>> r = tabular(df["regiao"])
    >>> print(r)
    """
    s = serie.dropna()
    n = len(s)
    if n == 0:
        raise ValueError("tabular(): série sem observações válidas.")

    contagem = s.value_counts(sort=True, ascending=False)
    freq_rel = (contagem / n * 100).round(2)
    freq_acum = freq_rel.cumsum().round(2)

    tabela = pd.DataFrame({
        "valor": contagem.index,
        "freq_absoluta": contagem.values,
        "freq_relativa_pct": freq_rel.values,
        "freq_acumulada_pct": freq_acum.values,
    })

    return TabulacaoResult(
        tabela=tabela,
        n=n,
        n_categorias=len(contagem),
        nome=str(serie.name) if serie.name is not None else "",
    )


# ---------------------------------------------------------------------------
# cruzar()
# ---------------------------------------------------------------------------

def cruzar(
    x: pd.Series,
    y: pd.Series,
    alpha: float = 0.05,
) -> ContingenciaResult:
    """
    Tabela de contingência com medidas de associação e testes de independência.

    Calcula:
    - Qui-quadrado de Pearson: χ² = sum((O_ij - E_ij)² / E_ij)
    - G² (Razão de Verossimilhança): G² = 2 * sum(O_ij * ln(O_ij / E_ij))
    - Phi (tabelas 2x2): phi = sqrt(χ² / n)
    - V de Cramér: V = sqrt(χ² / (n * (k-1))), k = min(linhas, colunas)
    - Coeficiente de Contingência: C = sqrt(χ² / (χ² + n))

    Parâmetros
    ----------
    x : pd.Series
        Variável das linhas.
    y : pd.Series
        Variável das colunas.
    alpha : float
        Nível para conclusão sobre independência.

    H0: x e y são independentes.

    Retorna
    -------
    ContingenciaResult
    """
    from scipy import stats as sp

    df_pair = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df_pair) < 4:
        raise ValueError("cruzar(): precisa de ao menos 4 pares completos.")

    tabela = pd.crosstab(df_pair["x"], df_pair["y"])
    obs = tabela.values.astype(float)
    n = int(obs.sum())
    linhas, colunas = obs.shape

    # Chi-quadrado de Pearson
    chi2, chi2_p, gl, esp = sp.chi2_contingency(obs, correction=False)

    # G² (razão de verossimilhança)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(esp > 0, obs / esp, 1.0)
        g2_vals = np.where(obs > 0, obs * np.log(ratio), 0.0)
    g2 = float(2 * g2_vals.sum())
    g2_p = float(sp.chi2.sf(g2, gl))

    # Medidas de associação
    k = min(linhas, colunas)
    v_cramer = float(np.sqrt(chi2 / (n * (k - 1)))) if k > 1 else 0.0
    coef_cont = float(np.sqrt(chi2 / (chi2 + n)))
    phi = float(np.sqrt(chi2 / n)) if linhas == 2 and colunas == 2 else None

    _, rejeita = _concluir(float(chi2_p), alpha, "x e y são independentes")

    tabela_esp = pd.DataFrame(
        esp.round(2), index=tabela.index, columns=tabela.columns
    )

    return ContingenciaResult(
        tabela=tabela,
        tabela_esperada=tabela_esp,
        n=n,
        chi2=float(chi2),
        chi2_pvalue=float(chi2_p),
        g2=g2,
        g2_pvalue=g2_p,
        gl=int(gl),
        phi=phi,
        v_cramer=v_cramer,
        coef_contingencia=coef_cont,
        rejeita_independencia=rejeita,
        alpha=alpha,
    )
