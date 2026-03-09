# Dessazonalização X-13 (X-13ARIMA-SEATS)

O **x13** não é uma fonte de dados: é uma **funcionalidade** do data_economist para **ajuste sazonal** de séries temporais. Usa o programa **X-13ARIMA-SEATS** (US Census Bureau): recebe uma série que já tenhas (por exemplo do BCB ou IBGE), monta a especificação (ficheiro .spc), executa o binário X-13 e devolve a série **dessazonalizada**, a **tendência**, o **irregular** e os **diagnósticos**. Equivale ao pacote **seasonal** do R.

**Quando usar:**
- **seas(series, ...)** — quando tem uma `pandas.Series` com `DatetimeIndex` mensal/trimestral e quer a série dessazonalizada e componentes.
- **init(project_root)** — uma vez por projeto, para garantir um ambiente virtual com o binário X-13 instalado (cria o diretório `venv` e instala `x13binary`).
- **final(modelo)**, **trend(modelo)**, **summary(modelo)** — para extrair resultados e resumos do objeto devolvido por `seas()`.

---

## Requisitos

1. **Python** 3.9+ com **pandas**.
2. **Binário X-13:** o pacote **x13binary** (PyPI) fornece o executável. O data_economist usa-o através de `x13.init()` (cria um `venv` no projeto e instala `x13binary` nesse venv) ou pode instalar manualmente: `pip install x13binary`.
3. **Série de entrada:** `pandas.Series` com **DatetimeIndex** e **frequência regular** (mensal ou trimestral). O X-13 não aceita datas em falta nem duplicadas; use `groupby(Grouper(freq="ME")).last()` se tiver mais de um valor por mês.

---

## Instalação e importação

```python
pip install data-economist x13binary
```

```python
from data_economist import x13
```

Na primeira utilização (ou se não tiver o binário no ambiente), execute **uma vez** no projeto:

```python
x13.init()   # ou x13.init(project_root="/caminho/do/projeto")
```

Isso cria o diretório **venv** na raiz do projeto e instala o **x13binary** dentro dele. O runner do x13 procura primeiro o executável nesse `venv`; se não existir, usa o do ambiente atual.

---

## Referência do programa X-13 e créditos

**Créditos dos cálculos:** O programa **X-13ARIMA-SEATS** é do **US Census Bureau** (método oficial de ajuste sazonal). O executável em Python é fornecido pelo pacote [x13binary](https://pypi.org/project/x13binary/) (PyPI). Os créditos dos algoritmos de dessazonalização são deles.

**O que é do data_economist:** O módulo **x13** não implementa o algoritmo; utiliza o binário X-13. A nossa contribuição é a integração em Python: construção do ficheiro de especificação (.spc), invocação do executável, leitura e interpretação dos ficheiros de saída (.udg, .html, .s11–.s13) e exposição dos resultados em objetos padronizados (`SeasonalResult`, série dessazonalizada, tendência, irregular). Ou seja, a manipulação, a interface e o resultado exposto ao utilizador são crédito do data_economist. Ver [Créditos e bibliotecas externas](creditos-bibliotecas.md).

| Programa | Descrição | Uso no pacote |
|----------|-----------|----------------|
| **X-13ARIMA-SEATS** | Programa do US Census Bureau para ajuste sazonal (regARIMA + SEATS). | O pacote gera o ficheiro .spc, chama o binário (via x13binary) e interpreta os ficheiros de saída (.udg, .html) para preencher o objeto de resultado. |

Documentação oficial:
- [X-13ARIMA-SEATS (Census Bureau)](https://www.census.gov/data/software/x13as.html)
- [x13binary (PyPI)](https://pypi.org/project/x13binary/)

---

## x13.init(project_root=None)

Garante que existe um diretório **venv** no projeto com **x13binary** instalado (e portanto o executável X-13 dentro do venv). Se o venv não existir, é criado; se o x13binary não estiver instalado nesse venv, é instalado.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **project_root** | `Path` ou `str` ou `None` | Raiz do projeto (onde ficará a pasta `venv`). Se `None`, é inferida a partir do diretório atual (procura `pyproject.toml` ou `src/data_economist`). |

### Retorno

- **Retorno:** `Path` — caminho do diretório `venv`.
- **Erros:** `FileNotFoundError` se o pip do venv ou o binário X-13 não forem encontrados após a instalação.

### Exemplo

```python
from data_economist import x13
from pathlib import Path

venv_path = x13.init(Path("."))
# venv_path == Path("c:/projeto/venv")
```

---

## x13.get_x13_bin_path(project_root=None)

Devolve o caminho do **executável X-13**. Procura primeiro no **venv** do projeto (diretório `venv`); se não existir aí, usa `x13binary.find_x13_bin()` do ambiente atual.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **project_root** | `Path` ou `str` ou `None` | Raiz do projeto. Se `None`, é inferida. |

### Retorno

- **Retorno:** `str` — caminho absoluto do executável (ex.: `.../venv/Scripts/x13as_html.exe` no Windows).
- **Erros:** `FileNotFoundError` se o binário não for encontrado (sugere executar `x13.init()` ou instalar `x13binary`).

---

## x13.seas(series, **kwargs)

Função principal: aplica o **ajuste sazonal X-13ARIMA-SEATS** à série e devolve um objeto **SeasonalResult** com a série original, a série dessazonalizada (final), tendência, irregular e diagnósticos.

### Parâmetros principais

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **series** | `pandas.Series` | Série temporal com `DatetimeIndex` mensal ou trimestral. |
| **title** | `str` | Título da série no ficheiro .spc (default `"series"`). |
| **transform_function** | `str` | `"auto"`, `"log"` ou `"none"` (default `"auto"`). |
| **automdl** | `bool` | Se `True`, o X-13 escolhe o modelo ARIMA automaticamente (default `True`). |
| **arima_model** | `str` ou `None` | Modelo fixo, ex. `"(0 1 1)(0 1 1)"`. Se definido, ignora a escolha automática. |
| **outlier** | `bool` | Deteção automática de outliers (default `True`). |
| **regression_aictest** | `list[str]` ou `None` | Ex. `["td", "easter"]` para testes AIC de regressores. |
| **estimate_maxiter** | `int` ou `None` | Número máximo de iterações na estimação. |
| **estimate_tol** | `float` ou `None` | Tolerância na estimação. |
| **x13_bin_path** | `str` ou `None` | Caminho do executável X-13. Se `None`, usa `get_x13_bin_path()`. |

### Retorno

- **Retorno:** **SeasonalResult** — objeto com atributos `.original`, `.final`, `.trend`, `.irregular`, `.udg`, `.messages`, `.spc_content`.

### Exemplo

```python
import pandas as pd
from data_economist import x13

x13.init()
idx = pd.date_range("2015-01", periods=72, freq="ME")
s = pd.Series([100 + i + 5 * (i % 12) for i in range(72)], index=idx)
modelo = x13.seas(s, title="minha_serie", transform_function="none")
```

---

## Objeto SeasonalResult

Resultado de `x13.seas()`. Atributos:

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| **original** | `pandas.Series` | Série original (entrada). |
| **final** | `pandas.Series` | Série dessazonalizada (equivalente a S 11 do X-13). |
| **trend** | `pandas.Series` ou `None` | Componente tendência (S 12). |
| **irregular** | `pandas.Series` ou `None` | Componente irregular (S 13). |
| **udg** | `dict` | Diagnósticos lidos do ficheiro .udg (nobs, transform, automdl, aic, bic, etc.). |
| **messages** | `list[str]` | Mensagens e avisos do X-13. |
| **spc_content** | `str` ou `None` | Conteúdo do ficheiro .spc usado. |

---

## x13.final(modelo) / original(modelo) / trend(modelo) / irregular(modelo)

Funções de conveniência que devolvem o atributo correspondente do **SeasonalResult**.

- **final(modelo)** → `modelo.final` (série dessazonalizada).
- **original(modelo)** → `modelo.original`.
- **trend(modelo)** → `modelo.trend` (pode ser `None`).
- **irregular(modelo)** → `modelo.irregular` (pode ser `None`).

---

## x13.udg(modelo)

Devolve o dicionário de **diagnósticos** (conteúdo do ficheiro .udg do X-13). Inclui, entre outros:

| Chave (exemplo) | Significado |
|-----------------|-------------|
| **nobs** | Número de observações. |
| **transform** | Transformação aplicada (No transformation, Log, etc.). |
| **automdl** | Modelo ARIMA escolhido automaticamente, formato (p d q)(P D Q). |
| **arimamdl** | Modelo ARIMA efectivamente estimado. |
| **converged** | Se a estimação convergiu (yes/no). |
| **aic**, **bic** | Critérios de informação (menor = melhor ajuste com penalização). |
| **automdl.best5.mdl01** | Um dos melhores modelos candidatos. |

Estes valores são **resultado** da estimação; não é possível alterá-los depois. Para obter outro resultado (outra transformação, outro modelo), é necessário **voltar a executar** `x13.seas()` com parâmetros diferentes (ex.: `transform_function="log"`, `arima_model="(1 0 1)(1 0 1)"`, `automdl=False`).

---

## x13.summary(modelo)

Devolve um **texto de resumo** do ajuste (número de observações, span, diagnósticos principais e mensagens). Útil para inspeção rápida.

### Exemplo

```python
print(x13.summary(modelo))
# X-13ARIMA-SEATS Seasonal Adjustment Result
# Original:  72 obs, span 2015-01-31 to 2021-12-31
# Final:     72 obs (dessazonalizada)
# Diagnósticos (udg): nobs, transform, automdl, arimamdl, converged, aic, bic, ...
```

---

## x13.get_series(modelo, key)

Devolve uma série do resultado pelo **nome**. Chaves suportadas na versão actual:

- `"original"` → `modelo.original`
- `"final"` → `modelo.final`
- `"trend"` ou `"seats.trend"` → `modelo.trend`
- `"irregular"` ou `"seats.irregular"` → `modelo.irregular`

Devolve `None` se a chave não existir.

---

## Exemplo completo: série do BCB (IPCA)

```python
import pandas as pd
from data_economist import bcb_sgs, x13

# 1) Dados do Banco Central (série 433 ou 1635)
dados = bcb_sgs.get(433)
df = pd.DataFrame(dados)
df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
df = df.dropna(subset=["valor"]).sort_values("data")
serie = df.groupby(pd.Grouper(key="data", freq="ME"))["valor"].last().dropna()

# 2) Ajuste sazonal
x13.init()
modelo = x13.seas(serie, title="IPCA")

# 3) Resultado e gráfico
resultado = pd.DataFrame({
    "data": x13.original(modelo).index,
    "valor": x13.original(modelo).values,
    "valor_dessaz": x13.final(modelo).values,
})
# resultado contém data, valor, valor_dessaz
```

---

## Exemplo: reexecutar com opções diferentes

Para “ajustar” o resultado (outra transformação ou modelo), reexecute `seas()` com outros argumentos:

```python
# Forçar transformação logarítmica
modelo_log = x13.seas(serie, transform_function="log")

# Fixar modelo ARIMA (sem escolha automática)
modelo_fixo = x13.seas(serie, arima_model="(1 0 1)(1 0 1)", automdl=False)
```

---

## Notas técnicas

- **Binário:** No Windows o x13binary instala **x13as_html.exe**, que produz saída em HTML. O parser do data_economist lê as tabelas S 11, S 12 e S 13 desse HTML para obter a série dessazonalizada, tendência e irregular. Os diagnósticos vêm do ficheiro **.udg** (formato texto chave: valor).
- **Precisão:** Os valores da série **final** (e trend/irregular) extraídos do HTML podem ter menos casas decimais do que a série original, pois o X-13 escreve no HTML com precisão limitada.
- **Diretório temporário:** Cada chamada a `seas()` usa um diretório temporário para o .spc e os ficheiros de saída; o utilizador não precisa de os gerir.
- **Versão:** Esta funcionalidade está disponível a partir da versão **0.5.0** do data_economist.

---

## Resumo rápido

| Objetivo | Função ou atributo |
|----------|--------------------|
| Garantir venv + binário X-13 | `x13.init()` |
| Obter caminho do executável | `x13.get_x13_bin_path()` |
| Ajuste sazonal | `modelo = x13.seas(series, ...)` |
| Série dessazonalizada | `x13.final(modelo)` ou `modelo.final` |
| Série original | `x13.original(modelo)` |
| Tendência / irregular | `x13.trend(modelo)`, `x13.irregular(modelo)` |
| Diagnósticos | `x13.udg(modelo)` ou `modelo.udg` |
| Resumo em texto | `x13.summary(modelo)` |
| Outra série por nome | `x13.get_series(modelo, "final")` |
