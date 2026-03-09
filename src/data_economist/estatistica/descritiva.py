"""
Estatística descritiva e resumos de distribuição.

Seção 3.1 do relatório EViews: resumo(), por_grupo(), ajustar_distribuicao().

Entrada esperada: pd.Series (numérica) ou pd.DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class ResumoResult:
    """
    Resultado do resumo estatístico de uma série.

    Atributos
    ---------
    n : int
        Número de observações válidas (sem NaN).
    media : float
    mediana : float
    minimo : float
    maximo : float
    std : float
        Desvio padrão amostral.
    variancia : float
    assimetria : float
        Assimetria de Fisher (skewness). Positiva = cauda à direita.
    curtose : float
        Curtose em excesso (kurtosis - 3). Normal = 0.
    jarque_bera : float
        Estatística Jarque-Bera: JB = n/6 * (S² + (K²/4)), testa normalidade.
    jb_pvalue : float
        p-valor do teste Jarque-Bera.
    percentis : dict
        P5, P25 (Q1), P75 (Q3), P95.
    iqr : float
        Amplitude interquartil (Q3 - Q1).
    cv : float
        Coeficiente de variação (std/média), em %.
    nome : str
        Nome da série analisada.
    """

    n: int
    media: float
    mediana: float
    minimo: float
    maximo: float
    std: float
    variancia: float
    assimetria: float
    curtose: float
    jarque_bera: float
    jb_pvalue: float
    percentis: dict
    iqr: float
    cv: float
    nome: str = ""

    @property
    def desvio_padrao(self) -> float:
        """Alias de std para uso em português."""
        return self.std

    @property
    def p5(self) -> float:
        return self.percentis["p5"]

    @property
    def p25(self) -> float:
        return self.percentis["p25"]

    @property
    def p75(self) -> float:
        return self.percentis["p75"]

    @property
    def p95(self) -> float:
        return self.percentis["p95"]

    def __str__(self) -> str:
        linhas = [
            f"Resumo: {self.nome}" if self.nome else "Resumo estatístico",
            f"  N          : {self.n}",
            f"  Média      : {self.media:.4f}",
            f"  Mediana    : {self.mediana:.4f}",
            f"  Mínimo     : {self.minimo:.4f}",
            f"  Máximo     : {self.maximo:.4f}",
            f"  Desvio Pad : {self.std:.4f}",
            f"  Assimetria : {self.assimetria:.4f}",
            f"  Curtose    : {self.curtose:.4f}",
            f"  Jarque-Bera: {self.jarque_bera:.4f}  (p={self.jb_pvalue:.4f})",
            f"  IQR        : {self.iqr:.4f}",
            f"  CV (%)     : {self.cv:.2f}",
        ]
        return "\n".join(linhas)

    def to_series(self) -> pd.Series:
        """Converte o resumo em pd.Series para exibição tabular."""
        return pd.Series({
            "n": self.n,
            "media": self.media,
            "mediana": self.mediana,
            "minimo": self.minimo,
            "maximo": self.maximo,
            "std": self.std,
            "variancia": self.variancia,
            "assimetria": self.assimetria,
            "curtose": self.curtose,
            "jarque_bera": self.jarque_bera,
            "jb_pvalue": self.jb_pvalue,
            "iqr": self.iqr,
            "cv_pct": self.cv,
            "p5": self.percentis.get("p5"),
            "p25": self.percentis.get("p25"),
            "p75": self.percentis.get("p75"),
            "p95": self.percentis.get("p95"),
        }, name=self.nome or "resumo")


@dataclass
class DistFitResult:
    """
    Resultado do ajuste de uma distribuição teórica a uma série.

    Atributos
    ---------
    distribuicao : str
        Nome da distribuição ajustada.
    params : dict
        Parâmetros estimados (loc, scale, shape se aplicável).
    ks_statistic : float
        Estatística de Kolmogorov-Smirnov do ajuste.
    ks_pvalue : float
        p-valor do KS (quão bem a distribuição ajusta).
    aic : float
        AIC = -2*logL + 2*k (menor = melhor).
    bic : float
        BIC = -2*logL + k*log(n).
    loglik : float
        Log-verossimilhança.
    """

    distribuicao: str
    params: dict
    ks_statistic: float
    ks_pvalue: float
    aic: float
    bic: float
    loglik: float

    def __str__(self) -> str:
        linhas = [
            f"Ajuste de distribuição: {self.distribuicao}",
            f"  Parâmetros : {self.params}",
            f"  KS         : {self.ks_statistic:.4f}  (p={self.ks_pvalue:.4f})",
            f"  Log-lik    : {self.loglik:.4f}",
            f"  AIC        : {self.aic:.4f}",
            f"  BIC        : {self.bic:.4f}",
        ]
        return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Distribuições disponíveis para ajuste
# ---------------------------------------------------------------------------

_DISTRIBUICOES = {
    "normal": "norm",
    "norm": "norm",
    "exponencial": "expon",
    "expon": "expon",
    "extreme_value": "gumbel_r",
    "gumbel": "gumbel_r",
    "logistica": "logistic",
    "logistic": "logistic",
    "chi2": "chi2",
    "chi_quadrado": "chi2",
    "weibull": "weibull_min",
    "gamma": "gamma",
    "lognormal": "lognorm",
    "t": "t",
}


# ---------------------------------------------------------------------------
# resumo()
# ---------------------------------------------------------------------------

def resumo(serie: pd.Series) -> ResumoResult:
    """
    Calcula o resumo estatístico completo de uma série numérica.

    Inclui: média, mediana, min, max, desvio padrão, variância,
    assimetria, curtose em excesso, teste Jarque-Bera, percentis,
    IQR e coeficiente de variação.

    Jarque-Bera: JB = n/6 * (S² + K²/4), onde S = assimetria e K = curtose excesso.
    Sob normalidade, JB ~ chi²(2). Rejeita normalidade se JB grande (p pequeno).

    Parâmetros
    ----------
    serie : pd.Series
        Série numérica. Valores NaN são removidos automaticamente.

    Retorna
    -------
    ResumoResult
    """
    if not pd.api.types.is_numeric_dtype(serie):
        raise ValueError("resumo(): a série deve ser numérica.")
    s = serie.dropna()
    n = len(s)
    if n < 3:
        raise ValueError("resumo(): precisa de ao menos 3 observações.")

    from scipy import stats as sp

    media = float(s.mean())
    mediana = float(s.median())
    minimo = float(s.min())
    maximo = float(s.max())
    std = float(s.std(ddof=1))
    variancia = float(s.var(ddof=1))
    assimetria = float(sp.skew(s, bias=False))
    curtose = float(sp.kurtosis(s, bias=False))  # excesso (normal = 0)

    jb_stat, jb_p = sp.jarque_bera(s)

    p5 = float(np.percentile(s, 5))
    p25 = float(np.percentile(s, 25))
    p75 = float(np.percentile(s, 75))
    p95 = float(np.percentile(s, 95))
    iqr = p75 - p25
    cv = (std / abs(media) * 100) if media != 0 else float("nan")

    return ResumoResult(
        n=n,
        media=media,
        mediana=mediana,
        minimo=minimo,
        maximo=maximo,
        std=std,
        variancia=variancia,
        assimetria=assimetria,
        curtose=curtose,
        jarque_bera=float(jb_stat),
        jb_pvalue=float(jb_p),
        percentis={"p5": p5, "p25": p25, "p75": p75, "p95": p95},
        iqr=iqr,
        cv=cv,
        nome=str(serie.name) if serie.name is not None else "",
    )


# ---------------------------------------------------------------------------
# por_grupo()
# ---------------------------------------------------------------------------

def por_grupo(
    df: pd.DataFrame,
    coluna_valor: str,
    coluna_grupo: str,
) -> dict[str, ResumoResult]:
    """
    Calcula resumos estatísticos separados por grupo.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com colunas de valor e de grupo.
    coluna_valor : str
        Nome da coluna com os valores numéricos.
    coluna_grupo : str
        Nome da coluna com os identificadores de grupo.

    Retorna
    -------
    dict[str, ResumoResult]
        Dicionário {nome_do_grupo: ResumoResult}.

    Exemplo
    -------
    >>> resultados = por_grupo(df, "vendas", "regiao")
    >>> print(resultados["Norte"])
    """
    if coluna_valor not in df.columns:
        raise ValueError(f"por_grupo(): coluna '{coluna_valor}' não encontrada.")
    if coluna_grupo not in df.columns:
        raise ValueError(f"por_grupo(): coluna '{coluna_grupo}' não encontrada.")

    resultados = {}
    for grupo, subdf in df.groupby(coluna_grupo):
        serie = subdf[coluna_valor].dropna().rename(f"{coluna_valor}[{grupo}]")
        try:
            resultados[str(grupo)] = resumo(serie)
        except ValueError:
            continue
    return resultados


# ---------------------------------------------------------------------------
# ajustar_distribuicao()
# ---------------------------------------------------------------------------

def ajustar_distribuicao(
    serie: pd.Series,
    distribuicao: str = "normal",
) -> DistFitResult:
    """
    Ajusta uma distribuição teórica à série por máxima verossimilhança.

    Distribuições disponíveis: normal, exponencial, extreme_value (Gumbel),
    logistica, chi2, weibull, gamma, lognormal, t.

    Parâmetros
    ----------
    serie : pd.Series
        Série numérica.
    distribuicao : str
        Nome da distribuição (padrão "normal").

    Retorna
    -------
    DistFitResult
        Inclui parâmetros estimados, KS de aderência, AIC e BIC.
    """
    s = serie.dropna().values
    n = len(s)
    if n < 5:
        raise ValueError("ajustar_distribuicao(): precisa de ao menos 5 observações.")

    dist_key = distribuicao.lower()
    if dist_key not in _DISTRIBUICOES:
        raise ValueError(
            f"ajustar_distribuicao(): distribuição '{distribuicao}' inválida. "
            f"Use uma de: {sorted(_DISTRIBUICOES.keys())}"
        )

    from scipy import stats as sp

    scipy_name = _DISTRIBUICOES[dist_key]
    dist_obj = getattr(sp, scipy_name)

    # Ajuste MLE
    params_tuple = dist_obj.fit(s)
    param_names = list(dist_obj.shapes.split(",")) if dist_obj.shapes else []
    param_names += ["loc", "scale"]
    params_dict = dict(zip(param_names, params_tuple))

    # Log-verossimilhança
    loglik = float(dist_obj.logpdf(s, *params_tuple).sum())
    k = len(params_tuple)
    aic = -2 * loglik + 2 * k
    bic = -2 * loglik + k * np.log(n)

    # KS de aderência
    ks_stat, ks_p = sp.kstest(s, scipy_name, args=params_tuple)

    return DistFitResult(
        distribuicao=distribuicao,
        params={k: round(float(v), 6) for k, v in params_dict.items()},
        ks_statistic=float(ks_stat),
        ks_pvalue=float(ks_p),
        aic=float(aic),
        bic=float(bic),
        loglik=loglik,
    )
