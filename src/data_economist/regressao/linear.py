"""
Modelos lineares: OLS, WLS, robusta, quantilica e diagnosticos OLS.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._resultado import RegResult


def _to_yx(y, X, add_const=True):
    y_s = pd.Series(y).astype(float)
    X_df = pd.DataFrame(X).astype(float)
    if add_const:
        X_df = X_df.copy()
        if "const" not in X_df.columns:
            X_df.insert(0, "const", 1.0)
    base = pd.concat([y_s.rename("y"), X_df], axis=1).dropna()
    y_ok = base["y"]
    X_ok = base.drop(columns=["y"])
    if len(y_ok) < max(8, X_ok.shape[1] + 2):
        raise ValueError("amostra insuficiente para estimacao")
    return y_ok, X_ok


def _pack_reg_result(fit, nome: str) -> RegResult:
    resid = pd.Series(fit.resid, index=fit.model.data.row_labels, name="resid")
    fitted = pd.Series(fit.fittedvalues, index=fit.model.data.row_labels, name="fitted")
    r2 = float(getattr(fit, "rsquared", np.nan))
    r2_adj = float(getattr(fit, "rsquared_adj", np.nan))
    return RegResult(
        modelo=nome,
        params=fit.params,
        pvalues=fit.pvalues,
        aic=float(getattr(fit, "aic", np.nan)),
        bic=float(getattr(fit, "bic", np.nan)),
        r2=r2,
        r2_adj=r2_adj,
        resid=resid,
        fitted=fitted,
        nobs=int(fit.nobs),
        extras={},
        fit_obj=fit,
    )


def ols(y, X, add_const=True, cov_type="nonrobust", cov_kwargs=None) -> RegResult:
    import statsmodels.api as sm

    y_ok, X_ok = _to_yx(y, X, add_const=add_const)
    fit = sm.OLS(y_ok, X_ok).fit()
    if cov_type != "nonrobust":
        fit = fit.get_robustcov_results(cov_type=cov_type, **(cov_kwargs or {}))
        fit.params = pd.Series(fit.params, index=X_ok.columns)
        fit.pvalues = pd.Series(fit.pvalues, index=X_ok.columns)
    out = _pack_reg_result(fit, f"OLS[{cov_type}]")

    # Extras: IC dos coeficientes, matriz de variância, betas padronizados, elasticidades, VIF
    out.extras["conf_int"] = fit.conf_int()
    out.extras["variancia_coef"] = fit.cov_params()
    out.extras["beta_padronizado"] = coeficientes_padronizados(y_ok, X_ok, out.params)
    out.extras["elasticidade_media"] = elasticidades(y_ok, X_ok, out.params, modo="media")
    out.extras["vif"] = vif(X_ok.drop(columns=["const"], errors="ignore"), add_const=add_const)
    return out


def wls(y, X, weights, add_const=True, cov_type="nonrobust", cov_kwargs=None) -> RegResult:
    import statsmodels.api as sm

    y_ok, X_ok = _to_yx(y, X, add_const=add_const)
    w = pd.Series(weights, index=pd.Series(y).index).astype(float)
    base = pd.concat([y_ok.rename("y"), X_ok, w.rename("w")], axis=1).dropna()
    y2 = base["y"]
    X2 = base.drop(columns=["y", "w"])
    w2 = base["w"]
    fit = sm.WLS(y2, X2, weights=w2).fit()
    if cov_type != "nonrobust":
        fit = fit.get_robustcov_results(cov_type=cov_type, **(cov_kwargs or {}))
        fit.params = pd.Series(fit.params, index=X2.columns)
        fit.pvalues = pd.Series(fit.pvalues, index=X2.columns)
    return _pack_reg_result(fit, f"WLS[{cov_type}]")


def robusta(y, X, add_const=True, m="huber") -> RegResult:
    import statsmodels.api as sm

    y_ok, X_ok = _to_yx(y, X, add_const=add_const)
    norm = sm.robust.norms.HuberT() if m.lower() == "huber" else sm.robust.norms.TukeyBiweight()
    fit = sm.RLM(y_ok, X_ok, M=norm).fit()
    return _pack_reg_result(fit, f"RLM[{m}]")


def quantilica(y, X, q=0.5, add_const=True) -> RegResult:
    import statsmodels.api as sm

    if not (0 < q < 1):
        raise ValueError("q deve estar em (0,1)")
    y_ok, X_ok = _to_yx(y, X, add_const=add_const)
    fit = sm.QuantReg(y_ok, X_ok).fit(q=q)
    out = _pack_reg_result(fit, f"QuantReg[q={q}]")
    out.extras["q"] = q
    return out


def vif(X, add_const=True) -> pd.Series:
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    X_df = pd.DataFrame(X).astype(float).dropna()
    if add_const and "const" not in X_df.columns:
        X_df = X_df.copy()
        X_df.insert(0, "const", 1.0)
    vals = [variance_inflation_factor(X_df.values, i) for i in range(X_df.shape[1])]
    return pd.Series(vals, index=X_df.columns, name="vif")


def coeficientes_padronizados(y, X, params: pd.Series) -> pd.Series:
    """
    Betas padronizados: beta_j * std(X_j) / std(y).
    """
    y_s = pd.Series(y).astype(float)
    X_df = pd.DataFrame(X).astype(float)
    sy = float(y_s.std(ddof=1))
    out = {}
    for c in X_df.columns:
        if c == "const":
            continue
        if c in params.index:
            sx = float(X_df[c].std(ddof=1))
            out[c] = float(params[c]) * (sx / sy) if sy > 0 else np.nan
    return pd.Series(out, name="beta_padronizado")


def elasticidades(y, X, params: pd.Series, modo="media") -> pd.Series:
    """
    Elasticidade aproximada: beta_j * (X_ref / Y_ref).
    modo='media' usa medias amostrais.
    """
    y_s = pd.Series(y).astype(float)
    X_df = pd.DataFrame(X).astype(float)
    if modo != "media":
        raise ValueError("modo suportado: 'media'")
    y_ref = float(y_s.mean())
    out = {}
    for c in X_df.columns:
        if c == "const":
            continue
        if c in params.index:
            x_ref = float(X_df[c].mean())
            out[c] = float(params[c]) * (x_ref / y_ref) if y_ref != 0 else np.nan
    return pd.Series(out, name="elasticidade_media")


def elipse_confianca(fit, p1: str, p2: str, alpha=0.05, n_points=200) -> pd.DataFrame:
    """
    Elipse de confianca (aprox. normal) para dois parametros de regressao.
    """
    import scipy.stats as sp

    params = pd.Series(fit.params)
    cov = pd.DataFrame(fit.cov_params(), index=params.index, columns=params.index)
    if p1 not in params.index or p2 not in params.index:
        raise ValueError("parametros nao encontrados no modelo")

    mu = np.array([params[p1], params[p2]], dtype=float)
    S = cov.loc[[p1, p2], [p1, p2]].values
    eigval, eigvec = np.linalg.eigh(S)
    c2 = sp.chi2.ppf(1 - alpha, df=2)

    t = np.linspace(0, 2 * np.pi, n_points)
    circle = np.vstack([np.cos(t), np.sin(t)])
    scale = np.diag(np.sqrt(np.maximum(eigval, 0) * c2))
    pts = (eigvec @ scale @ circle).T + mu
    return pd.DataFrame(pts, columns=[p1, p2])

