# Fonte Regressao (`data_economist.regressao`)

Modulo para regressao e estimacao de equacao unica.

**Creditos:** OLS, WLS, regressao robusta (Huber/Bisquare), quantilica, VIF e ARDL utilizam o pacote [statsmodels](https://www.statsmodels.org/). Pode usar pela nossa API (resultados em dataclasses padronizadas) ou diretamente pelo statsmodels. NLS usa scipy; TAR/SETAR/STAR e PDL sao implementacoes proprias. Ver [Creditos e bibliotecas externas](creditos-bibliotecas.md).

## Funcoes principais

### Lineares

- `ols(y, X, add_const=True, cov_type="nonrobust", cov_kwargs=None)`
- `wls(y, X, weights, add_const=True, cov_type="nonrobust", cov_kwargs=None)`
- `robusta(y, X, add_const=True, m="huber")`
- `quantilica(y, X, q=0.5, add_const=True)`
- `vif(X, add_const=True)`
- `coeficientes_padronizados(y, X, params)`
- `elasticidades(y, X, params, modo="media")`
- `elipse_confianca(fit, p1, p2, alpha=0.05)`

### Nao linear

- `nls(y, x, func, p0)`

### Selecao

- `stepwise(y, X, metodo="forward|backward|both", criterio="aic|bic", max_vars=None)`

### Dinamicos

- `pdl(y, x, lags=4, grau=2, add_const=True)`
- `ardl(y, X, lags_y=1, lags_x=1, trend="c")`
- `ardl_bounds(resultado_ardl)`

### Limiar

- `tar(y, lag=1, threshold=None)`
- `setar(y, lag=1, threshold=None)`
- `star(y, lag=1, gamma_grid=None, c_grid=None)` (logistico)

## Exemplos

```python
from data_economist import regressao as reg

# OLS
r = reg.ols(y, X, cov_type="HC1")
print(r.params)
print(r.extras["beta_padronizado"])
print(r.extras["elasticidade_media"])

# Quantilica (mediana)
rq = reg.quantilica(y, X, q=0.5)

# NLS: y = a * exp(b*x)
def f(x, a, b):
    return a * np.exp(b * x)

rnls = reg.nls(y=y, x=x, func=f, p0=[1.0, 0.1])

# Stepwise
sw = reg.stepwise(y, X, metodo="both", criterio="aic")
print(sw.selecionadas)

# PDL
rpdl = reg.pdl(y, x, lags=4, grau=2)
print(rpdl.extras["coef_lags"])

# STAR
rstar = reg.star(y, lag=1)
print(rstar.extras["gamma"], rstar.extras["c"])
```

## Objetos de retorno

- `RegResult`
- `NLSResult`
- `StepwiseResult`
- `ThresholdResult`

## Observacoes

- `cov_type` em `ols` e `wls` aceita robustez de erros (`HC*`, `HAC`, `cluster`).
- `ols` inclui extras: IC de coeficientes, matriz de variancia dos coeficientes,
  betas padronizados, elasticidades e VIF.
- `ardl_bounds` depende da disponibilidade da API na versao atual do statsmodels.
- `tar` e `setar` implementam versao basica em dois regimes; `star` implementa transicao suave logistica.

