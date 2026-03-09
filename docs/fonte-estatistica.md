# Módulo estatistica

O módulo **estatistica** reúne análises estatísticas baseadas nas funcionalidades da seção 3 do EViews: estatística descritiva, testes de normalidade, correlação, testes de hipótese, tabelas de contingência e análise multivariada.

Não obtém dados da internet — opera sobre séries e DataFrames que já existem.

---

## Importação

```python
from data_economist import estatistica
# ou
import data_economist as de
# de.estatistica.resumo(serie)
```

Todas as funções públicas estão diretamente no namespace `estatistica`:

```python
import data_economist.estatistica as est
```

---

## 3.1 Estatística descritiva (`estatistica.descritiva`)

### `resumo(serie)` → `ResumoResult`

Calcula estatísticas básicas de uma série numérica.

```python
r = est.resumo(serie)

r.n              # int — observações válidas
r.media          # float
r.mediana        # float
r.minimo         # float
r.maximo         # float
r.desvio_padrao  # float (alias: r.std)
r.variancia      # float
r.assimetria     # float — Fisher skewness
r.curtose        # float — curtose em excesso (normal = 0)
r.jarque_bera    # float — estatística JB
r.jb_pvalue      # float — p-valor do teste JB
r.p5             # float — percentil 5
r.p25            # float — 1º quartil
r.p75            # float — 3º quartil
r.p95            # float — percentil 95
r.iqr            # float — amplitude interquartil
r.cv             # float — coeficiente de variação (%)
```

```python
print(r)             # resumo formatado
r.to_series()        # pd.Series para exibição tabular
```

### `por_grupo(df, coluna_valor, coluna_grupo)` → `dict[str, ResumoResult]`

Resumo estatístico por categoria.

```python
r = est.por_grupo(df, coluna_valor="preco", coluna_grupo="regiao")

for grupo, resumo in r.items():
    print(grupo, resumo.media)
```

### `ajustar_distribuicao(serie, distribuicao="normal")` → `DistFitResult`

Ajusta uma distribuição teórica por MLE (máxima verossimilhança).

```python
r = est.ajustar_distribuicao(serie, "normal")

r.distribuicao   # str
r.parametros     # dict — parâmetros estimados (loc, scale, etc.)
r.log_likelihood # float
r.aic            # float — AIC = -2*logL + 2*k
r.bic            # float — BIC = -2*logL + k*ln(n)
r.ks_statistic   # float — aderência KS
r.ks_pvalue      # float
```

Distribuições disponíveis: `"normal"`, `"exponencial"`, `"extreme_value"` (Gumbel), `"logistica"`, `"chi2"`, `"weibull"`, `"gamma"`, `"lognormal"`, `"t"`.

---

## 3.2 Testes de normalidade (`estatistica.normalidade`)

Todos retornam `TesteResult` com os atributos:

```python
r.statistic     # float — estatística do teste
r.pvalue        # float
r.metodo        # str — nome do teste
r.hipotese_nula # str — enunciado de H0
r.conclusao     # str — texto automático de conclusão
r.rejeita_h0    # bool — True se H0 rejeitada ao nível alpha
r.alpha         # float (padrão 0.05)
print(r)        # resumo formatado
```

### Funções disponíveis

```python
# Kolmogorov-Smirnov (com parâmetros estimados ou fixos)
r = est.ks(serie)
r = est.ks(serie, distribuicao="logistica")

# Lilliefors (KS corrigido para parâmetros estimados — recomendado para normalidade)
r = est.lilliefors(serie)

# Anderson-Darling (mais sensível às caudas)
r = est.anderson_darling(serie)

# Cramer-von Mises
r = est.cramer_von_mises(serie)

# Watson (variante do Cramer-von Mises invariante à localização)
r = est.watson(serie)
```

---

## 3.3 Correlação e covariância (`estatistica.correlacao`)

### Correlações bivariadas

Todas retornam `CorrelacaoResult`:

```python
r.coeficiente         # float — valor do coeficiente
r.pvalue              # float
r.metodo              # str
r.n                   # int — pares válidos
r.intervalo_confianca # tuple(lo, hi) ou None
r.rejeita_h0          # bool — rejeita H0: correlação = 0?
```

```python
# Pearson (relação linear)
r = est.pearson(x, y)

# Spearman (monotônica, baseado em postos)
r = est.spearman(x, y)

# Kendall Tau-b (concordância, com tratamento de empates)
r = est.kendall_b(x, y)

# Kendall Tau-a (sem correção de empates)
r = est.kendall_a(x, y)

# Correlação parcial (remove efeito de variáveis de controle)
r = est.parcial(df, x="x1", y="x2", controles=["x3", "x4"])
```

### Matrizes

```python
# Matriz de covariância (ddof=1)
cov = est.covariancia(df)   # pd.DataFrame n×n

# Matriz de correlação
corr = est.matriz_correlacao(df)                    # Pearson (padrão)
corr = est.matriz_correlacao(df, metodo="spearman") # ou "kendall"
```

---

## 3.4 Testes de hipótese (`estatistica.testes`)

Todos retornam `TesteResult`.

### t-test

```python
# Uma amostra: testa se média = valor_ref
r = est.ttest(serie, valor_ref=0.0)

# Duas amostras independentes (Welch, não assume variâncias iguais)
r = est.ttest(grupo_a, grupo_b)

# Pareado
r = est.ttest(antes, depois, pareado=True)
```

### ANOVA e equivalentes não paramétricos

```python
# ANOVA de um fator (assume normalidade e homogeneidade)
r = est.anova(grupo_a, grupo_b, grupo_c)

# Kruskal-Wallis (não paramétrico — alternativa ao ANOVA)
r = est.kruskal_wallis(grupo_a, grupo_b, grupo_c)

# van der Waerden (scores normais — entre ANOVA e Kruskal-Wallis em poder)
r = est.van_der_waerden(grupo_a, grupo_b, grupo_c)

# Teste da mediana (qui-quadrado)
r = est.mediana_chi2(grupo_a, grupo_b, grupo_c)
```

### Testes para duas amostras

```python
# Mann-Whitney U (independentes, não paramétrico)
r = est.mann_whitney(x, y)

# Wilcoxon (postos sinalizados — pareado ou uma amostra)
r = est.wilcoxon(x)           # uma amostra: testa mediana = 0
r = est.wilcoxon(antes, depois)  # pareado
```

### Homogeneidade de variâncias

```python
# Teste F (duas amostras, assume normalidade)
r = est.teste_f(x, y)

# Bartlett (múltiplos grupos, assume normalidade)
r = est.bartlett(grupo_a, grupo_b, grupo_c)

# Levene (robusto a desvios de normalidade)
r = est.levene(grupo_a, grupo_b, grupo_c)

# Brown-Forsythe (mais robusto que Levene — usa mediana)
r = est.brown_forsythe(grupo_a, grupo_b, grupo_c)

# Siegel-Tukey (dispersão, não paramétrico)
r = est.siegel_tukey(x, y)
```

---

## 3.5 Tabelas de contingência (`estatistica.contingencia`)

### `tabular(serie)` → `TabulacaoResult`

Frequências absolutas e relativas de uma série categórica.

```python
r = est.tabular(df["regiao"])

r.n             # int — total
r.n_categorias  # int
r.tabela        # pd.DataFrame com: valor, freq_absoluta, freq_relativa_pct, freq_acumulada_pct
print(r)
```

### `cruzar(x, y)` → `ContingenciaResult`

Tabela de contingência cruzada com testes de independência e medidas de associação.

```python
r = est.cruzar(df["produto"], df["regiao"])

r.tabela                # pd.DataFrame — frequências observadas
r.tabela_esperada       # pd.DataFrame — frequências esperadas sob independência
r.n                     # int
r.chi2                  # float — qui-quadrado de Pearson
r.chi2_pvalue           # float
r.g2                    # float — G² (razão de verossimilhança)
r.g2_pvalue             # float
r.gl                    # int — graus de liberdade
r.phi                   # float ou None — válido apenas para tabelas 2×2
r.v_cramer              # float — V de Cramér ∈ [0, 1]
r.coef_contingencia     # float — coeficiente de contingência de Pearson
r.rejeita_independencia # bool
print(r)
```

---

## 3.6 Análise multivariada (`estatistica.multivariada`)

### `pca(df, n_componentes=None, padronizar=True)` → `PCAResult`

Análise de Componentes Principais por decomposição SVD.

```python
r = est.pca(df)

r.autovalores          # pd.Series — variância de cada componente
r.variancia_explicada  # pd.Series — proporção explicada (0 a 1)
r.variancia_acumulada  # pd.Series — proporção acumulada
r.cargas               # pd.DataFrame — loadings: variáveis × componentes
r.scores               # pd.DataFrame — scores: observações × componentes
r.n_componentes        # int
r.padronizado          # bool
print(r)
```

```python
# Reter apenas 2 componentes
r = est.pca(df, n_componentes=2)

# Sem padronização (decompõe covariância, não correlação)
r = est.pca(df, padronizar=False)
```

### `fatorial(df, n_fatores=2, rotacao="varimax", metodo="ml")` → `FatorialResult`

Análise Fatorial Exploratória com rotação.

```python
r = est.fatorial(df, n_fatores=2)

r.cargas         # pd.DataFrame — cargas fatoriais: variáveis × fatores
r.unicidades     # pd.Series — variância específica de cada variável
r.comunalidades  # pd.Series — variância explicada pelos fatores comuns (1 - unicidade)
r.scores         # pd.DataFrame ou None
r.rotacao        # str — rotação usada
r.converged      # bool
print(r)
```

Rotações disponíveis: `"varimax"` (padrão), `"quartimax"`, `"oblimin"`, `"promax"`, `"equamax"`, `None`.

Métodos de estimação: `"ml"` (máxima verossimilhança, padrão) ou `"pa"` (eixos principais iterados).

---

## Fluxo típico: análise completa de uma série

```python
from data_economist import bcb_sgs, estatistica as est
import pandas as pd

# 1. Obter e preparar a série
dados = bcb_sgs.get(433, "2010-01-01")
df = pd.DataFrame(dados)
df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
serie = df.set_index("data")["valor"].astype(float).resample("ME").last().dropna()

# 2. Resumo descritivo
resumo = est.resumo(serie)
print(resumo)

# 3. Testar normalidade
print(est.lilliefors(serie))

# 4. Correlação com outra série
serie_b = ...  # outra série
r_corr = est.pearson(serie, serie_b)
print(f"Pearson r={r_corr.coeficiente:.3f}  p={r_corr.pvalue:.4f}")
```

## Fluxo típico: PCA em DataFrame multivariado

```python
import pandas as pd
import data_economist.estatistica as est

df = pd.read_csv("indicadores.csv", index_col=0)

# PCA
r = est.pca(df, n_componentes=3)
print(r)
print(r.cargas)

# Quanto cada CP explica
print(r.variancia_explicada * 100)  # em %

# Scores das observações (índices sintéticos)
scores = r.scores
```

---

## Tipos de retorno

| Função | Retorno |
|--------|---------|
| `resumo()` | `ResumoResult` |
| `por_grupo()` | `dict[str, ResumoResult]` |
| `ajustar_distribuicao()` | `DistFitResult` |
| `ks()`, `lilliefors()`, `anderson_darling()`, `cramer_von_mises()`, `watson()` | `TesteResult` |
| `pearson()`, `spearman()`, `kendall_b()`, `kendall_a()`, `parcial()` | `CorrelacaoResult` |
| `covariancia()`, `matriz_correlacao()` | `pd.DataFrame` |
| `ttest()`, `anova()`, `wilcoxon()`, `mann_whitney()`, etc. | `TesteResult` |
| `tabular()` | `TabulacaoResult` |
| `cruzar()` | `ContingenciaResult` |
| `pca()` | `PCAResult` |
| `fatorial()` | `FatorialResult` |

Todos os dataclasses têm `print(r)` formatado e atributos documentados nos docstrings.
