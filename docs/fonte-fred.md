# Fonte: FRED — Federal Reserve Economic Data

O módulo `fred` permite coletar dados do banco de dados econômico do **Federal Reserve Bank of St. Louis** — mais de 800.000 séries temporais cobrindo indicadores macroeconômicos dos EUA e globais.

- Site: https://fred.stlouisfed.org/
- Documentação da API: https://fred.stlouisfed.org/docs/api/fred/
- Registro de token (gratuito): https://fred.stlouisfed.org/docs/api/api_key.html

---

## Configuração do Token

É obrigatório configurar um token de API para usar o módulo FRED.

1. **Obtenha um token gratuito** em: https://fred.stlouisfed.org/docs/api/api_key.html  
2. **Crie um arquivo chamado `.env`** na raiz do projeto (a pasta onde você roda o código ou onde está o `data_economist`). Se o arquivo já existir (por exemplo para `TOKEN_EIA`), apenas edite-o.  
3. **Adicione uma linha** com o nome da variável e o valor do token (sem aspas, sem espaços em volta do `=`):

```
TOKEN_FRED=seu_token_aqui
```

O módulo lê automaticamente a variável `TOKEN_FRED` (fallback: `FRED_API_KEY`). Se o token não estiver configurado ou estiver inválido, as funções do `fred` lançam um erro explicando que é preciso criar ou editar o `.env` e adicionar `TOKEN_FRED`.

---

## Importação

```python
from data_economist import fred
```

---

## Funções Disponíveis

### `fred.get` — Observações de uma série

```python
fred.get(
    series_id,
    date_init=None,
    date_end=None,
    units=None,
    frequency=None,
    aggregation_method=None,
    limit=100_000,
    sort_order="asc",
    timeout=30,
    api_key=None,
) -> list[dict]
```

Retorna a série histórica como lista de `{"date": "YYYY-MM-DD", "value": float | None}`.
Valores ausentes (`"."` na API) são convertidos para `None`.

**Exemplos:**

```python
# Série completa
cpi = fred.get("CPIAUCSL")

# Com intervalo de datas
cpi = fred.get("CPIAUCSL", date_init="2010-01-01", date_end="2024-12-31")

# Com datetime
from datetime import datetime
cpi = fred.get("CPIAUCSL", date_init=datetime(2010, 1, 1))

# Variação percentual ano a ano
cpi_yoy = fred.get("CPIAUCSL", units="pc1")

# Agregação anual por média
cpi_anual = fred.get("CPIAUCSL", frequency="a", aggregation_method="avg")

# VIX diário
vix = fred.get("VIXCLS")

# Taxa de juros (Fed Funds)
juros = fred.get("FEDFUNDS", date_init="2000-01-01")

# Câmbio USD/CNY
cambio = fred.get("DEXCHUS")
```

**Parâmetro `units` (transformações disponíveis):**

| Valor | Descrição |
|---|---|
| `lin` | Nível (padrão) |
| `chg` | Variação absoluta |
| `ch1` | Variação absoluta em relação ao mesmo período do ano anterior |
| `pch` | Variação percentual |
| `pc1` | Variação percentual em relação ao mesmo período do ano anterior |
| `pca` | Taxa de crescimento anual composta |
| `cch` | Variação percentual composta continuamente |
| `cca` | Taxa anual composta continuamente |
| `log` | Logaritmo natural |

**Parâmetro `frequency` (agregação de frequência):**

| Valor | Frequência |
|---|---|
| `d` | Diária |
| `w` | Semanal |
| `bw` | Quinzenal |
| `m` | Mensal |
| `q` | Trimestral |
| `sa` | Semestral |
| `a` | Anual |

---

### `fred.metadados` — Informações descritivas da série

```python
fred.metadados(series_id, timeout=30, api_key=None) -> dict
```

Retorna um dicionário com informações sobre a série: título, frequência, unidade, ajuste sazonal, período coberto e notas metodológicas.

```python
meta = fred.metadados("CPIAUCSL")

print(meta["title"])             # Consumer Price Index for All Urban Consumers...
print(meta["frequency"])         # Monthly
print(meta["units"])             # Index 1982-1984=100
print(meta["seasonal_adjustment"])  # Seasonally Adjusted
print(meta["observation_start"]) # 1947-01-01
print(meta["observation_end"])   # 2024-12-01
```

**Campos retornados:**

| Campo | Descrição |
|---|---|
| `id` | Identificador da série |
| `title` | Nome descritivo completo |
| `frequency` | Frequência textual (ex.: `Monthly`) |
| `frequency_short` | Frequência curta (ex.: `M`) |
| `units` | Unidade de medida |
| `seasonal_adjustment` | Descrição do ajuste sazonal |
| `seasonal_adjustment_short` | Sigla do ajuste sazonal (`SA`, `NSA`, etc.) |
| `observation_start` | Data da primeira observação disponível |
| `observation_end` | Data da última observação disponível |
| `last_updated` | Última atualização no FRED |
| `notes` | Notas metodológicas (pode estar ausente) |

---

### `fred.buscar` — Busca de séries por texto

```python
fred.buscar(
    texto,
    limit=100,
    order_by="popularity",
    sort_order="desc",
    filter_variable=None,
    filter_value=None,
    tag_names=None,
    timeout=30,
    api_key=None,
) -> list[dict]
```

Busca séries pelo nome ou descrição. Retorna lista de dicionários com os mesmos campos de `metadados()`.

```python
# Busca geral por popularidade
series = fred.buscar("consumer price index", limit=20)
for s in series:
    print(s["id"], "-", s["title"])

# Filtrar por frequência mensal
series = fred.buscar("unemployment", filter_variable="frequency", filter_value="Monthly")

# Busca com tags específicas
series = fred.buscar("interest rate", tag_names="usa;monthly")
```

---

### `fred.categorias` — Informações de categoria

```python
fred.categorias(category_id=0, timeout=30, api_key=None) -> dict
```

O FRED organiza séries em uma hierarquia de categorias. `category_id=0` é a raiz.

```python
# Raiz da hierarquia
raiz = fred.categorias()          # {"id": 0, "name": "Categories", "parent_id": 0}

# Categoria Macroeconomics (ID 125)
macro = fred.categorias(125)
```

---

### `fred.series_categoria` — Séries de uma categoria

```python
fred.series_categoria(category_id, limit=100, timeout=30, api_key=None) -> list[dict]
```

Lista as séries pertencentes a uma categoria FRED.

```python
series = fred.series_categoria(125, limit=50)
for s in series:
    print(s["id"], s["frequency"], "-", s["title"])
```

---

### `fred.tags` — Tags de uma série

```python
fred.tags(series_id, timeout=30, api_key=None) -> list[dict]
```

Retorna as tags associadas a uma série, úteis para descobrir séries relacionadas.

```python
t = fred.tags("CPIAUCSL")
nomes = [x["name"] for x in t]
# ['bls', 'consumer price index', 'cpi', 'inflation', 'monthly', 'nsa', ...]
```

---

### `fred.release` — Informações de um release

```python
fred.release(release_id, timeout=30, api_key=None) -> dict
```

Um *release* é uma publicação oficial (ex.: Employment Situation, CPI). Cada série pertence a um release.

```python
emp = fred.release(10)
print(emp["name"])  # Employment Situation
print(emp["link"])  # https://www.bls.gov/news.release/empsit.htm
```

---

### `fred.series_release` — Séries de um release

```python
fred.series_release(release_id, limit=100, timeout=30, api_key=None) -> list[dict]
```

```python
series = fred.series_release(10, limit=50)
```

---

## Constante `SERIES_FRED`

O módulo expõe a constante `SERIES_FRED` com séries organizadas por frequência e grupo temático:

```python
fred.SERIES_FRED["daily"]["pol_mon"]
# ['DTWEXBGS', 'DTWEXAFEGS', 'DTWEXEMEGS', 'VIXCLS', 'SP500']

fred.SERIES_FRED["monthly"]["pol_mon"]
# ['CPIAUCSL', 'CPILFESL', 'CUSR0000SAS', 'UNRATE', 'DFEDTARU', 'DFEDTARL', 'FEDFUNDS', 'RTWEXBGS']

fred.SERIES_FRED["monthly"]["petrol"]
# ['WPU0543', 'WPU0531']

fred.SERIES_FRED["monthly"]["bk"]
# Bens de capital: turbinas, bombas, compressores, aeronaves, transformadores...

fred.SERIES_FRED["monthly"]["min_sid"]
# Minério de ferro e siderurgia: PPI aço, placas, fio-máquina...

fred.SERIES_FRED["monthly"]["quimicos"]
# PPI químicos: resinas, plásticos, especialidades...

fred.SERIES_FRED["quarterly"]["pol_mon"]
# ['CIU2013000000000I']  # Custo unitário do trabalho
```

Exemplo de uso:

```python
# Coletar todas as séries diárias de política monetária
for sid in fred.SERIES_FRED["daily"]["pol_mon"]:
    dados = fred.get(sid)
    print(f"{sid}: {len(dados)} observações")
```

---

## Tratamento de Erros

| Situação | Exceção |
|---|---|
| TOKEN_FRED ausente ou vazio | `ValueError` — a mensagem explica criar/editar o `.env` e adicionar `TOKEN_FRED=seu_token` |
| Token inválido (HTTP 401/403 ou mensagem de erro da API) | `ValueError` — a mensagem orienta a verificar o `.env` e o link para obter token |
| Série não encontrada (HTTP 404) | `FredError` |
| Limite de requisições (HTTP 429) | `FredError` |
| Erro interno da API (HTTP 5xx) | `FredError` |
| JSON com `error_message` genérico | `FredError` |

```python
from data_economist.fred import FredError

try:
    dados = fred.get("SERIE_INVALIDA", api_key="tok")
except FredError as e:
    print(f"Erro FRED: {e}")
except ValueError as e:
    print(f"Problema de autenticação: {e}")
```

---

## Nota sobre Valores Ausentes

A API FRED usa o caractere `"."` para indicar observações não disponíveis ou não divulgadas.
O módulo converte automaticamente esses valores para `None`.

```python
dados = fred.get("DEXCHUS")  # USD/CNY pode ter missings em feriados
missings = [d for d in dados if d["value"] is None]
print(f"Missings: {len(missings)}")
```

---

## Séries de Referência por Tema

### Política Monetária e Câmbio (diário)
- `DTWEXBGS` — US Dollar Index amplo (Broad)
- `DTWEXAFEGS` — US Dollar Index economias avançadas
- `DTWEXEMEGS` — US Dollar Index mercados emergentes
- `VIXCLS` — VIX (volatilidade implícita do S&P 500)
- `SP500` — S&P 500

### Inflação e Emprego (mensal)
- `CPIAUCSL` — CPI todos os itens, sazonalmente ajustado
- `CPILFESL` — CPI core (ex-alimentos e energia), SA
- `CUSR0000SAS` — CPI serviços, SA
- `UNRATE` — Taxa de desemprego (%)

### Juros (mensal)
- `FEDFUNDS` — Fed Funds Effective Rate
- `DFEDTARU` / `DFEDTARL` — Fed Funds target (limites superior e inferior)
- `RTWEXBGS` — Real US Dollar Index Broad

### Câmbio
- `DEXCHUS` — USD/CNY (diário)
