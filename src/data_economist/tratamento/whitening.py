"""
Pré-branqueamento (whitening) de séries temporais.

Ajusta um modelo AR(p) à série e devolve os resíduos, que são aproximadamente
ruído branco (sem autocorrelação). Usado como etapa de pré-processamento antes
de calcular estatísticas de variância de longo prazo ou testes de independência.

Seleção automática da ordem p por AIC quando lags=None.

Entrada esperada: pd.Series com DatetimeIndex.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class WhiteResult:
    """
    Resultado do pré-branqueamento por modelo AR(p).

    Atributos
    ---------
    original : pd.Series
        Série original fornecida.
    serie_branca : pd.Series
        Resíduos do modelo AR(p) — série pré-branqueada.
    lags_usados : int
        Ordem p do modelo AR efetivamente estimado.
    coeficientes : pd.Series
        Coeficientes phi_1 ... phi_p do modelo AR (excluindo a constante).
    aic : float
        AIC do modelo selecionado.
    params : dict
        Parâmetros da estimação (inclui constante, lags_max testados etc.).
    """

    original: pd.Series
    serie_branca: pd.Series
    lags_usados: int
    coeficientes: pd.Series
    aic: float
    params: dict = field(default_factory=dict)


def whitening(
    series: pd.Series,
    lags: Optional[int] = None,
    lags_max: Optional[int] = None,
    criterio: str = "aic",
) -> WhiteResult:
    """
    Pré-branqueamento por modelo AR(p).

    Ajusta um modelo autorregressivo de ordem p à série e devolve os resíduos
    (série branqueada), os coeficientes estimados e os diagnósticos.

    O modelo AR(p) é:
        y_t = c + phi_1 * y_{t-1} + ... + phi_p * y_{t-p} + e_t

    onde e_t é a série branca resultante.

    Parâmetros
    ----------
    series : pd.Series
        Série temporal com DatetimeIndex.
    lags : int, opcional
        Ordem fixa do modelo AR. Se None, a ordem é selecionada automaticamente
        pelo critério especificado.
    lags_max : int, opcional
        Ordem máxima a testar na seleção automática.
        Padrão: min(12, n // 4), onde n é o número de observações.
    criterio : str
        Critério de seleção automática: "aic" ou "bic" (padrão "aic").

    Retorna
    -------
    WhiteResult
        .serie_branca : resíduos do modelo AR (série pré-branqueada)
        .lags_usados  : ordem p efetivamente usada
        .coeficientes : pd.Series com phi_1 ... phi_p
        .aic          : AIC do modelo

    Exemplo
    -------
    >>> resultado = whitening(serie_mensal)
    >>> branca = serie_branca(resultado)
    >>> print(resultado.lags_usados)
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError(
            "whitening(): a série deve ter DatetimeIndex. "
            f"Tipo atual: {type(series.index).__name__}"
        )

    s = series.dropna()
    n = len(s)

    if n < 6:
        raise ValueError(
            "whitening(): a série precisa de ao menos 6 observações."
        )

    if criterio not in ("aic", "bic"):
        raise ValueError(
            f"whitening(): criterio '{criterio}' inválido. Use 'aic' ou 'bic'."
        )

    from statsmodels.tsa.ar_model import AutoReg, ar_select_order

    lags_max_used = lags_max if lags_max is not None else min(12, n // 4)
    lags_max_used = max(lags_max_used, 1)

    if lags is not None:
        # Ordem fixa
        p = lags
    else:
        # Seleção automática por AIC/BIC
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sel = ar_select_order(s, maxlag=lags_max_used, ic=criterio, old_names=False)
        p = sel.ar_lags[-1] if sel.ar_lags else 1

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = AutoReg(s, lags=p, old_names=False)
        fit = model.fit()

    residuos = fit.resid
    serie_branca = pd.Series(residuos.values, index=residuos.index, name="serie_branca")

    # Coeficientes AR (excluindo a constante)
    params_all = fit.params
    coef_names = [name for name in params_all.index if name.startswith(s.name or "") or "L" in name]
    # Extrair apenas os coeficientes de defasagem (excluir "const")
    coef_ar = params_all.drop(labels=[k for k in params_all.index if k == "const"], errors="ignore")
    coeficientes = pd.Series(coef_ar.values, index=coef_ar.index, name="coeficientes")

    return WhiteResult(
        original=series,
        serie_branca=serie_branca,
        lags_usados=p,
        coeficientes=coeficientes,
        aic=float(fit.aic),
        params={
            "lags": p,
            "lags_max_testados": lags_max_used,
            "criterio": criterio,
            "n_obs": n,
        },
    )


def serie_branca(resultado: WhiteResult) -> pd.Series:
    """Devolve a série pré-branqueada (resíduos do modelo AR)."""
    return resultado.serie_branca
