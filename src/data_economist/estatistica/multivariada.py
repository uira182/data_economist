"""
Análise multivariada: PCA e análise fatorial.

Funções:
    pca()      — Análise de Componentes Principais
    fatorial() — Análise Fatorial Exploratória
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class PCAResult:
    """
    Resultado da Análise de Componentes Principais.

    Atributos
    ---------
    autovalores : pd.Series
        Autovalores (variância de cada componente).
    variancia_explicada : pd.Series
        Proporção da variância explicada por componente (0 a 1).
    variancia_acumulada : pd.Series
        Proporção da variância acumulada.
    cargas : pd.DataFrame
        Matriz de cargas (loadings): variáveis × componentes.
    scores : pd.DataFrame
        Scores das observações: obs × componentes.
    n_componentes : int
        Número de componentes retidos.
    n_obs : int
        Número de observações utilizadas.
    n_variaveis : int
        Número de variáveis de entrada.
    padronizado : bool
        True se os dados foram padronizados antes da decomposição.
    """

    autovalores: pd.Series
    variancia_explicada: pd.Series
    variancia_acumulada: pd.Series
    cargas: pd.DataFrame
    scores: pd.DataFrame
    n_componentes: int
    n_obs: int
    n_variaveis: int
    padronizado: bool

    def __str__(self) -> str:
        linhas = [
            "Análise de Componentes Principais (PCA)",
            f"  Variáveis        : {self.n_variaveis}",
            f"  Observações      : {self.n_obs}",
            f"  Componentes      : {self.n_componentes}",
            f"  Padronizado      : {self.padronizado}",
            "",
            "Variância explicada:",
        ]
        for i, (ev, ve, va) in enumerate(zip(
            self.autovalores, self.variancia_explicada, self.variancia_acumulada
        ), 1):
            linhas.append(f"  CP{i:02d}  autoval={ev:.4f}  expl={ve*100:.1f}%  acum={va*100:.1f}%")
        return "\n".join(linhas)


@dataclass
class FatorialResult:
    """
    Resultado da Análise Fatorial Exploratória.

    Atributos
    ---------
    cargas : pd.DataFrame
        Matriz de cargas fatoriais: variáveis × fatores.
    unicidades : pd.Series
        Unicidades (variância específica de cada variável).
    comunalidades : pd.Series
        Comunalidades = 1 - unicidade.
    scores : pd.DataFrame ou None
        Scores fatoriais estimados (se calculados).
    rotacao : str
        Nome da rotação utilizada.
    metodo : str
        Método de estimação ("ml" ou "pa").
    n_fatores : int
        Número de fatores.
    n_obs : int
        Número de observações.
    n_variaveis : int
        Número de variáveis.
    converged : bool
        True se o algoritmo de estimação convergiu.
    """

    cargas: pd.DataFrame
    unicidades: pd.Series
    comunalidades: pd.Series
    scores: Optional[pd.DataFrame]
    rotacao: str
    metodo: str
    n_fatores: int
    n_obs: int
    n_variaveis: int
    converged: bool

    def __str__(self) -> str:
        linhas = [
            "Análise Fatorial",
            f"  Variáveis   : {self.n_variaveis}",
            f"  Observações : {self.n_obs}",
            f"  Fatores     : {self.n_fatores}",
            f"  Método      : {self.metodo}",
            f"  Rotação     : {self.rotacao}",
            f"  Convergiu   : {self.converged}",
            "",
            "Cargas fatoriais:",
            self.cargas.round(4).to_string(),
            "",
            "Comunalidades:",
            self.comunalidades.round(4).to_string(),
        ]
        return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validar_df(df: pd.DataFrame, nome: str, min_obs: int = 5) -> pd.DataFrame:
    """Remove linhas com NaN e valida tamanho mínimo."""
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(num_cols) < 2:
        raise ValueError(f"{nome}(): o DataFrame precisa ter ao menos 2 colunas numéricas.")
    dfn = df[num_cols].dropna()
    if len(dfn) < min_obs:
        raise ValueError(f"{nome}(): precisa de ao menos {min_obs} observações completas.")
    return dfn


# ---------------------------------------------------------------------------
# PCA
# ---------------------------------------------------------------------------

def pca(
    df: pd.DataFrame,
    n_componentes: Optional[int] = None,
    padronizar: bool = True,
) -> PCAResult:
    """
    Análise de Componentes Principais (PCA).

    Decomposição espectral da matriz de correlação (padronizar=True) ou
    de covariância (padronizar=False).

    Cada componente é uma combinação linear das variáveis originais que
    maximiza a variância explicada, ortogonalmente às componentes anteriores.

    Parâmetros
    ----------
    df : pd.DataFrame
        Colunas numéricas. Linhas com NaN são removidas.
    n_componentes : int, opcional
        Número de componentes a reter. Se None: retém todos.
    padronizar : bool
        Se True (padrão): decompõe a matriz de correlação (variáveis em escala
        comparável). Se False: decompõe a matriz de covariância.

    Retorna
    -------
    PCAResult
    """
    dfn = _validar_df(df, "pca")
    n_obs, n_var = dfn.shape

    x = dfn.values.astype(float)
    x_mean = x.mean(axis=0)
    x_c = x - x_mean

    if padronizar:
        x_std = x.std(axis=0, ddof=1)
        x_std[x_std == 0] = 1.0
        x_c = x_c / x_std

    # Decomposição por valor singular
    U, s, Vt = np.linalg.svd(x_c, full_matrices=False)
    autovalores_todos = (s ** 2) / (n_obs - 1)
    var_total = autovalores_todos.sum()
    var_expl = autovalores_todos / var_total if var_total > 0 else autovalores_todos

    k = n_componentes if n_componentes is not None else n_var
    k = max(1, min(k, n_var))

    comp_names = [f"CP{i+1:02d}" for i in range(k)]
    var_names = dfn.columns.tolist()

    cargas_mat = Vt[:k].T  # shape: (n_var, k)
    scores_mat = x_c @ Vt[:k].T  # shape: (n_obs, k)

    autovalores = pd.Series(autovalores_todos[:k], index=comp_names, name="autovalor")
    var_explicada = pd.Series(var_expl[:k], index=comp_names, name="var_explicada")
    var_acumulada = var_explicada.cumsum()
    var_acumulada.name = "var_acumulada"

    cargas = pd.DataFrame(cargas_mat, index=var_names, columns=comp_names)
    scores = pd.DataFrame(scores_mat, index=dfn.index, columns=comp_names)

    return PCAResult(
        autovalores=autovalores,
        variancia_explicada=var_explicada,
        variancia_acumulada=var_acumulada,
        cargas=cargas,
        scores=scores,
        n_componentes=k,
        n_obs=n_obs,
        n_variaveis=n_var,
        padronizado=padronizar,
    )


# ---------------------------------------------------------------------------
# Fatorial
# ---------------------------------------------------------------------------

def fatorial(
    df: pd.DataFrame,
    n_fatores: int = 2,
    rotacao: str = "varimax",
    metodo: str = "ml",
) -> FatorialResult:
    """
    Análise Fatorial Exploratória.

    Modela cada variável observada como combinação linear de fatores latentes
    comuns mais um fator específico (unicidade):
        X = L * F + E
    onde L são as cargas fatoriais, F os fatores comuns e E os específicos.

    Parâmetros
    ----------
    df : pd.DataFrame
        Colunas numéricas. Linhas com NaN são removidas.
    n_fatores : int
        Número de fatores latentes.
    rotacao : str
        Método de rotação: "varimax" (padrão), "quartimax", "promax", "oblimin",
        "equamax", ou None para sem rotação.
    metodo : str
        Método de estimação: "ml" (máxima verossimilhança, padrão) ou
        "pa" (eixos principais — iterado).

    Retorna
    -------
    FatorialResult

    Notas
    -----
    Usa statsmodels.multivariate.factor.Factor. Para método "ml" pode falhar
    a convergir com dados altamente correlacionados ou n_fatores muito alto.
    """
    try:
        from statsmodels.multivariate.factor import Factor  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "fatorial() requer statsmodels >= 0.13.0. Execute: pip install statsmodels"
        ) from exc

    dfn = _validar_df(df, "fatorial", min_obs=max(10, n_fatores * 3))
    n_obs, n_var = dfn.shape

    if n_fatores < 1:
        raise ValueError("fatorial(): n_fatores deve ser >= 1.")
    if n_fatores >= n_var:
        raise ValueError("fatorial(): n_fatores deve ser menor que o número de variáveis.")

    x = dfn.values.astype(float)
    nomes = dfn.columns.tolist()

    metodo_sm = metodo.lower()
    if metodo_sm not in ("ml", "pa"):
        raise ValueError("fatorial(): metodo deve ser 'ml' ou 'pa'.")

    rot_sm = rotacao if rotacao is not None else None

    try:
        modelo = Factor(x, n_factor=n_fatores, method=metodo_sm)
        resultado = modelo.fit(maxiter=200, tol=1e-8)
        converged = bool(getattr(resultado, "mle_retvals", {}).get("converged", True))
    except Exception as e:
        raise RuntimeError(f"fatorial(): estimação falhou — {e}") from e

    # Cargas antes da rotação
    cargas_raw = resultado.loadings  # shape: (n_var, n_fatores)

    # Rotação
    if rot_sm is not None:
        try:
            from statsmodels.multivariate.factor_rotation import rotate_factors  # type: ignore
            rot_map = {
                "varimax": "varimax",
                "quartimax": "quartimax",
                "oblimin": "oblimin",
                "promax": "promax",
                "equamax": "equamax",
            }
            rot_key = rot_map.get(rot_sm.lower(), rot_sm.lower())
            cargas_rot, _ = rotate_factors(cargas_raw, rot_key)
        except Exception:
            cargas_rot = cargas_raw
    else:
        cargas_rot = cargas_raw

    fat_names = [f"F{i+1}" for i in range(n_fatores)]
    cargas_df = pd.DataFrame(cargas_rot, index=nomes, columns=fat_names)

    unicidades_arr = resultado.uniqueness
    unicidades = pd.Series(unicidades_arr, index=nomes, name="unicidade")
    comunalidades = pd.Series(1.0 - unicidades_arr, index=nomes, name="comunalidade")

    # Scores (se possível)
    try:
        scores_arr = resultado.factor_scoring_matrix
        if scores_arr is not None:
            x_std = (x - x.mean(axis=0)) / np.maximum(x.std(axis=0, ddof=1), 1e-12)
            scores_mat = x_std @ scores_arr
            scores_df: Optional[pd.DataFrame] = pd.DataFrame(
                scores_mat, index=dfn.index, columns=fat_names
            )
        else:
            scores_df = None
    except Exception:
        scores_df = None

    return FatorialResult(
        cargas=cargas_df,
        unicidades=unicidades,
        comunalidades=comunalidades,
        scores=scores_df,
        rotacao=rotacao if rotacao is not None else "nenhuma",
        metodo=metodo_sm,
        n_fatores=n_fatores,
        n_obs=n_obs,
        n_variaveis=n_var,
        converged=converged,
    )
