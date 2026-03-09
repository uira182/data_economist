# Módulo tratamento

O módulo **tratamento** contém ferramentas de processamento e análise de séries temporais (filtros de ciclo e tendência, suavização exponencial, conversão de frequência, whitening). Não obtém dados da internet — aplica-se a séries que já existem (por exemplo, obtidas do BCB ou IBGE).

**Créditos:** Os filtros (Hodrick-Prescott, Baxter-King, Christiano-Fitzgerald), a suavização exponencial (SES, Holt, Holt-Winters, ETS) e o whitening AR(p) utilizam o pacote [statsmodels](https://www.statsmodels.org/). Pode usar pela nossa API (nomes e resultados padronizados) ou diretamente pelo statsmodels. Ver [Créditos e bibliotecas externas](creditos-bibliotecas.md).

---

## Importação

```python
from data_economist import tratamento
# ou
import data_economist as de
# de.tratamento.hp(serie)
```

---

## 2.3 Filtros de ciclo e tendência (`tratamento.filtros`)

Extraem componentes de tendência e ciclo de séries temporais.

### `hp(serie, lambda_=None)` — Filtro Hodrick-Prescott

```python
r = tratamento.hp(serie)

r.ciclo      # pd.Series — componente cíclico
r.tendencia  # pd.Series — componente de tendência
r.lambda_    # float — parâmetro lambda utilizado
```

O lambda é inferido automaticamente pela frequência da série (1600 para trimestral, 14400 para mensal, 6,25 para anual) ou pode ser passado manualmente.

```python
# Lambda fixo
r = tratamento.hp(serie, lambda_=1600)

# Lambda inferido automaticamente
r = tratamento.hp(serie_trimestral)
```

### `bk(serie, low=6, high=32, K=12)` — Filtro Baxter-King

```python
r = tratamento.bk(serie)

r.ciclo      # pd.Series — ciclo de negócios extraído
r.tendencia  # pd.Series — tendência (série original - ciclo)
```

Parâmetros `low` e `high` definem a banda de frequência em trimestres. `K` é a ordem do filtro (truncamento da série nos extremos).

### `cf(serie, low=6, high=32, drift=False)` — Filtro Christiano-Fitzgerald

```python
r = tratamento.cf(serie)

r.ciclo      # pd.Series
r.tendencia  # pd.Series
```

Versão assimétrica (usa toda a amostra em cada ponto), geralmente mais precisa que o BK nas bordas da série.

---

## 2.4 Suavização exponencial (`tratamento.suavizacao`)

### `ses(serie, alpha=None)` — Suavização Exponencial Simples

```python
r = tratamento.ses(serie)

r.suavizado      # pd.Series — série suavizada
r.alpha          # float — parâmetro de suavização (0 < alpha < 1)
r.sse            # float — soma dos erros ao quadrado
```

### `des(serie, alpha=None, beta=None)` — Suavização Exponencial Dupla

```python
r = tratamento.des(serie)
```

Captura tendência linear. Se `alpha` e `beta` forem `None`, são otimizados automaticamente.

### `holt(serie, alpha=None, beta=None)` — Método de Holt (tendência)

```python
r = tratamento.holt(serie)

r.suavizado      # pd.Series
r.alpha          # float
r.beta           # float
```

### `holt_winters(serie, m=None, tipo="add", alpha=None, beta=None, gamma=None)` — Holt-Winters

```python
# Sazonalidade aditiva (padrão) — para séries mensais:
r = tratamento.holt_winters(serie_mensal)

# Sazonalidade multiplicativa:
r = tratamento.holt_winters(serie_mensal, tipo="mul")

r.suavizado  # pd.Series
r.alpha      # float
r.beta       # float
r.gamma      # float
r.m          # int — períodos sazonais inferidos
```

O período sazonal `m` é inferido automaticamente da frequência do índice DatetimeIndex.

### `ets(serie, error="add", trend=None, seasonal=None, m=None)` — ETS

```python
# ETS automático (seleciona o melhor modelo por AIC):
r = tratamento.ets(serie)

# ETS com configuração explícita:
r = tratamento.ets(serie, error="add", trend="add", seasonal="add", m=12)

r.suavizado  # pd.Series
r.aic        # float — critério de informação de Akaike
```

### Previsão a partir de qualquer resultado de suavização

```python
from data_economist.tratamento import forecast

r = tratamento.holt_winters(serie)
prox_12 = forecast(r, steps=12)   # pd.Series com 12 períodos à frente
```

---

## 2.5 Conversão de frequência (`tratamento.frequencia`)

### `para_frequencia(serie, freq, metodo="mean")` — Agregação ou interpolação

```python
from data_economist import tratamento

# Diário → Mensal (agregação)
mensal = tratamento.para_frequencia(serie_diaria, "ME", metodo="mean")
mensal = tratamento.para_frequencia(serie_diaria, "ME", metodo="sum")
mensal = tratamento.para_frequencia(serie_diaria, "ME", metodo="last")

# Mensal → Diário (interpolação)
diario = tratamento.para_frequencia(serie_mensal, "D", metodo="linear")
diario = tratamento.para_frequencia(serie_mensal, "D", metodo="cubic")
diario = tratamento.para_frequencia(serie_mensal, "D", metodo="pchip")
```

**Métodos de agregação:** `"mean"`, `"sum"`, `"first"`, `"last"`, `"max"`, `"min"`

**Métodos de interpolação:** `"linear"`, `"quadratic"`, `"cubic"`, `"ffill"`, `"pchip"`, `"spline"`

A direção (agregar vs. interpolar) é detectada automaticamente; mas se você passar um método de agregação, o sentido é forçado para agregação independentemente da frequência de destino.

---

## 2.6 Pré-branqueamento (`tratamento.whitening`)

### `whitening(serie, lags=None, criterio="aic")` — Whitening AR(p)

Remove autocorrelação ajustando um modelo AR(p) e retorna os resíduos.

```python
r = tratamento.whitening(serie)

r.residuos        # pd.Series — resíduos (série "branca")
r.coeficientes    # list[float] — coeficientes AR estimados
r.lags            # int — ordem p do modelo
r.aic             # float
```

### `serie_branca(r)` — extrator

```python
from data_economist.tratamento import serie_branca

residuos = serie_branca(r)   # pd.Series
```

---

## Fluxo típico

```python
from data_economist import bcb_sgs, tratamento
import pandas as pd

# 1. Obter série
dados = bcb_sgs.get(433, "2015-01-01")
df = pd.DataFrame(dados)
df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
serie = df.set_index("data")["valor"].astype(float).resample("ME").last().dropna()

# 2. Filtrar tendência e ciclo
r_hp = tratamento.hp(serie)
print(r_hp.tendencia.tail())
print(r_hp.ciclo.tail())

# 3. Suavizar
r_hw = tratamento.holt_winters(serie)
print(r_hw.suavizado.tail())

# 4. Converter para trimestral
trimestral = tratamento.para_frequencia(serie, "QE")

# 5. Pré-branquear antes de correlograma
r_white = tratamento.whitening(serie)
print(r_white.lags, r_white.aic)
```

---

## Tipos de retorno

| Função | Retorno |
|--------|---------|
| `hp()`, `bk()`, `cf()` | `FilterResult` |
| `ses()`, `des()`, `holt()`, `holt_winters()`, `ets()` | `SmoothResult` |
| `para_frequencia()` | `pd.Series` |
| `whitening()` | `WhiteResult` |

Todos os dataclasses de resultado podem ser inspecionados com `print(r)` ou `vars(r)`.
