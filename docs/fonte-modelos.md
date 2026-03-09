# Fonte Modelos (`data_economist.modelos`)

O modulo `modelos` oferece modelos univariados de series temporais.
Ele oferece ajuste, diagnostico, selecao automatica e previsao para ARIMA e variantes.

**Créditos:** Os cálculos de AR, MA, ARMA, ARIMA, SARIMA, ARMAX, testes de raiz unitária (ADF, PP, KPSS, Zivot-Andrews), ACF/PACF e Ljung-Box são realizados pelo pacote [statsmodels](https://www.statsmodels.org/). O ARFIMA usa estimador GPH e diferença fracionária implementados no data_economist; o ajuste ARMA final usa o ARIMA do statsmodels. Pode utilizar os mesmos modelos de duas formas: **(1)** pela nossa API — `modelos.ar()`, `modelos.arima()`, `modelos.prever()`, etc., com nomes e resultados padronizados — ou **(2)** diretamente pelo statsmodels (`from statsmodels.tsa.arima.model import ARIMA`, etc.) quando precisar de opções avançadas ou do objeto nativo. Ver [Créditos e bibliotecas externas](creditos-bibliotecas.md).

## 1) Importacao

```python
from data_economist import modelos
```

## 2) Familia ARIMA

### AR, MA, ARMA

```python
r_ar = modelos.ar(serie, lags=2)
r_ma = modelos.ma(serie, lags=1)
r_arma = modelos.arma(serie, p=1, q=1)
```

### ARIMA e SARIMA

```python
r_arima = modelos.arima(serie, p=1, d=1, q=1)
r_sarima = modelos.sarima(serie, p=1, d=1, q=1, P=1, D=0, Q=1, s=12)
```

### ARMAX (com exogenas)

```python
r_armax = modelos.armax(serie, p=1, d=0, q=1, exog=df_exog)
```

## 3) Previsao

Com qualquer `ModeloResult` da familia ARIMA:

```python
prev = modelos.prever(r_arima, steps=12)
print(prev.valores.tail())
print(prev.ic_lower.tail(), prev.ic_upper.tail())
```

Retorno:
- `valores`: previsao pontual
- `ic_lower`, `ic_upper`: intervalo de confianca
- `steps`, `alpha`

## 4) Selecao de modelo

### Busca automatica

```python
melhor = modelos.auto_arima(
    serie,
    max_p=4,
    max_q=4,
    max_d=2,
    criterio="aic",
    stepwise=True,
)
print(melhor.modelo, melhor.aic)
```

### Tabela de criterios por ordens

```python
tabela = modelos.criterios(serie, ordens=[(0, 1), (1, 0), (1, 1), (2, 1)], d=0)
print(tabela)
```

## 5) Diagnostico de autocorrelacao

```python
diag = modelos.acf_pacf(serie, nlags=24)
print(diag.acf[:5])
print(diag.pacf[:5])
print(diag.ljung_box.tail())
```

## 6) Raiz unitaria e estacionariedade

```python
r_adf = modelos.adf(serie, trend="ct")
r_pp = modelos.pp(serie, trend="ct")
r_kpss = modelos.kpss(serie, trend="c")
r_za = modelos.za(serie, trend="ct")
```

Interpretacao rapida:
- `adf` e `pp`: H0 = raiz unitaria (nao estacionaria)
- `kpss`: H0 = estacionaria
- `za`: raiz unitaria com quebra estrutural endogena

## 7) Memoria longa (ARFIMA)

### Estimador GPH para `d`

```python
d_info = modelos.gph(serie)
print(d_info["d"], d_info["ic_95"])
```

### ARFIMA

```python
r_arfima = modelos.arfima(serie, p=1, q=1)      # estima d por GPH
r_arfima_fix = modelos.arfima(serie, p=1, q=1, d=0.25)
print(r_arfima.params["d_fracionario"])
```

## 8) Objetos de retorno

Os resultados principais sao:
- `ModeloResult`
- `PrevisaoResult`
- `RaizResult`
- `ACFResult`

Todos podem ser importados por:

```python
from data_economist.modelos import ModeloResult, PrevisaoResult, RaizResult, ACFResult
```

## 9) Fluxo recomendado

1. Diagnosticar serie (`adf`, `kpss`, `acf_pacf`)
2. Ajustar candidatos (`arima`, `sarima`, `armax`)
3. Comparar (`criterios`, `auto_arima`)
4. Validar residuos
5. Projetar (`prever`)

