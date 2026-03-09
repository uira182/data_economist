# Fonte EIA — U.S. Energy Information Administration

O módulo **eia** do data_economist permite consultar dados energéticos da **EIA** (U.S. Energy Information Administration) via API v2. É **obrigatório** dispor de um **token de API** (registo em [eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php)), que deve ser definido no ficheiro **.env** como **TOKEN_EIA=seu_token**.

**Quando usar cada função:**
- **get(url)** / **get_data(url)** — quando já tem a URL completa do endpoint EIA.
- **get_steo(series_id, frequency)** — dados STEO (petróleo, químicos, etc.) por série e frequência (monthly/quarterly/annual).
- **get_petroleum(route, series, frequency)** — dados Petroleum (preços, stocks) por rota, série e frequência (weekly/daily).
- **get_by_landing(sector, frequency)** — todos os dados do mapeamento (setor + frequência) num único dicionário.

---

## Obtenção do token

1. Aceda a **[https://www.eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php)**.
2. Preencha o formulário (nome, e-mail, organização).
3. O token será enviado para o seu e-mail.
4. Na **raiz do seu projeto** (ou no diretório de trabalho), crie ou edite o ficheiro **`.env`** e adicione:

   ```
   TOKEN_EIA=seu_token_aqui
   ```

5. O `.env` não deve ser commitado no Git (adicione-o ao `.gitignore`).

Sem o token, qualquer função do módulo (`get`, `get_data`, `get_steo`, `get_petroleum`, `get_by_landing`) levanta `ValueError` com indicação do registo e link da documentação EIA.

---

## Instalação e importação

```python
from data_economist import eia
```

Requisito: variável de ambiente **TOKEN_EIA** definida (por exemplo via ficheiro `.env`). O pacote opcional **python-dotenv** carrega automaticamente o `.env` se estiver instalado.

---

## API utilizada

| API | Base URL | Uso no pacote |
|-----|----------|---------------|
| **EIA Open Data API v2** | https://api.eia.gov/v2 | `eia.get(url)` — GET com URL completa; o parâmetro `api_key` é adicionado automaticamente. |

Documentação e registo:
- [EIA Open Data](https://www.eia.gov/opendata/)
- [Registo do token](https://www.eia.gov/opendata/register.php)
- [Documentação técnica](https://www.eia.gov/opendata/documentation.php)

---

## eia.get(url, timeout=30, api_key=None)

Faz um GET à URL indicada, adicionando o parâmetro **api_key** (token) se ainda não estiver na URL. O token é lido de **TOKEN_EIA** no ambiente (ou do `.env`), salvo se for passado `api_key` explicitamente.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **url** | `str` | URL completa do endpoint EIA (ex.: `https://api.eia.gov/v2/steo/data/?frequency=monthly&data[0]=value&facets[seriesId][]=PATC_WORLD&...`). |
| **timeout** | `int` | Timeout em segundos (default 30). |
| **api_key** | `str` ou `None` | Token de API. Se `None`, usa **TOKEN_EIA** do ambiente. |

### Retorno

- **Retorno:** `dict` — resposta JSON da API (estrutura típica: `{"response": {"data": [...], ...}}`).
- **Erros:** `ValueError` se o token não estiver definido; `requests.HTTPError` em falha HTTP.

### Exemplo

```python
from data_economist import eia

url = (
    "https://api.eia.gov/v2/steo/data/?frequency=monthly&data[0]=value"
    "&facets[seriesId][]=PATC_WORLD&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"
)
resposta = eia.get(url)
# resposta["response"]["data"] — lista de registos (period, value, seriesId, etc.)
```

---

## eia.get_data(url, timeout=30, api_key=None)

Igual a `eia.get()`, mas devolve apenas a **lista de registos** (`response.response.data`). Útil para uso direto em análise.

### Parâmetros

Idênticos a `eia.get(url, timeout, api_key)`.

### Retorno

- **Retorno:** `list[dict]` — lista de registos (cada um com `period`, `value` e identificador de série). Lista vazia se a API não devolver dados.

### Exemplo

```python
from data_economist import eia

url = "https://api.eia.gov/v2/steo/data/?frequency=monthly&data[0]=value&facets[seriesId][]=PATC_WORLD&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=100"
dados = eia.get_data(url)
for r in dados[:5]:
    print(r["period"], r["value"])
```

---

## eia.get_steo(series_id, frequency="monthly", offset=0, length=5000, ...)

Obtém dados do endpoint **STEO** (Short-Term Energy Outlook) passando apenas o **identificador da série** e a **frequência**. A URL é montada internamente.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **series_id** | `str` | Código da série STEO (ex.: `PATC_WORLD`, `NGHHUUS`, `ZOTOIUS`). |
| **frequency** | `str` | `monthly`, `quarterly` ou `annual`. |
| **offset** | `int` | Deslocamento na paginação (default 0). |
| **length** | `int` | Número de registos (default 5000). |
| **timeout** | `int` | Timeout em segundos (default 30). |
| **api_key** | `str` ou `None` | Token EIA; se `None`, usa TOKEN_EIA do ambiente. |

### Retorno e erros

- **Retorno:** `list[dict]` — lista de registos (`period`, `value`, `seriesId`, etc.).
- **Erros:** `ValueError` se o token não estiver definido; `requests.HTTPError` ou `ValueError` (403/token inválido) em falha HTTP.

### Exemplo

```python
from data_economist import eia

dados = eia.get_steo("PATC_WORLD", "monthly")
dados = eia.get_steo("NGHHUUS", "quarterly", length=100)
# Séries: eia.SERIES_STEO["petroleo_monthly"], eia.SERIES_STEO["quimicos_monthly"], etc.
```

---

## eia.get_petroleum(route, series, frequency, offset=0, length=5000, ...)

Obtém dados do endpoint **Petroleum** passando a **rota**, o **código da série** e a **frequência** (ex.: preços diários, stocks semanais).

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **route** | `str` | Sub-rota: `cons/wpsup`, `sum/sndw`, `pri/spt`, `pnp/wprodrb`, `pnp/wiup`, `move/wkly`. |
| **series** | `str` | Código da série (ex.: `WGFUPUS2`, `EER_EPMRU_PF4_RGC_DPG`). |
| **frequency** | `str` | `weekly` ou `daily`. |
| **offset**, **length**, **timeout**, **api_key** | — | Idênticos a `get_steo`. |

### Retorno e erros

- **Retorno:** `list[dict]` — lista de registos (`period`, `value`, `series`, etc.).
- **Erros:** Idênticos a `get_steo` (token em falta ou inválido, falha HTTP).

### Exemplo

```python
from data_economist import eia

dados = eia.get_petroleum("pri/spt", "EER_EPMRU_PF4_RGC_DPG", "daily")
dados = eia.get_petroleum("cons/wpsup", "WGFUPUS2", "weekly")
# Pares (route, series): eia.SERIES_PETROLEUM["petroleo_weekly"], eia.SERIES_PETROLEUM["petroleo_daily"]
```

---

## eia.get_by_landing(sector, frequency, timeout=30, api_key=None)

Obtém **todos** os dados do mapeamento para um **setor** e **frequência**. Usa internamente `SERIES_STEO` e `SERIES_PETROLEUM`.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **sector** | `str` | `petroleo`, `quimicos` ou `min_sid`. |
| **frequency** | `str` | `monthly`, `quarterly`, `annual` (STEO) ou `weekly`, `daily` (Petroleum). |
| **timeout** | `int` | Timeout por requisição (default 30). |
| **api_key** | `str` ou `None` | Token EIA; se `None`, usa TOKEN_EIA do ambiente. |

### Retorno

- **Retorno:** `dict[str, list[dict]]` — cada chave é um identificador de série; o valor é a lista de registos dessa série.

### Exemplo

```python
from data_economist import eia

tudo = eia.get_by_landing("petroleo", "monthly")
# tudo["PATC_WORLD"], tudo["PAPR_OPEC"], ...

tudo = eia.get_by_landing("petroleo", "weekly")
tudo = eia.get_by_landing("quimicos", "quarterly")
```

---

## Mapeamentos

Os dicionários **SERIES_STEO** e **SERIES_PETROLEUM** contêm o mapeamento de URLs por setor e frequência. Podem ser usados para iterar sobre as séries sem construir URLs à mão.

| Constante | Conteúdo |
|-----------|----------|
| **eia.SERIES_STEO** | `dict`: chave = `"setor_frequency"` (ex.: `petroleo_monthly`, `quimicos_quarterly`); valor = lista de `series_id` (STEO). |
| **eia.SERIES_PETROLEUM** | `dict`: chave = `"setor_frequency"` (ex.: `petroleo_weekly`, `petroleo_daily`); valor = lista de `(route, series)`. |

Exemplo:

```python
from data_economist import eia

for series_id in eia.SERIES_STEO["petroleo_monthly"]:
    dados = eia.get_steo(series_id, "monthly")

for route, series in eia.SERIES_PETROLEUM["petroleo_daily"]:
    dados = eia.get_petroleum(route, series, "daily")
```

---

## Resumo

| Função | Uso |
|--------|-----|
| `get(url)` | GET à URL EIA (com token); devolve o JSON completo. |
| `get_data(url)` | GET à URL EIA; devolve apenas `response.response.data` (lista de registos). |
| `get_steo(series_id, frequency)` | Dados STEO por série e frequência (monthly/quarterly/annual). |
| `get_petroleum(route, series, frequency)` | Dados Petroleum por rota, série e frequência (weekly/daily). |
| `get_by_landing(sector, frequency)` | Todos os dados do mapeamento para setor e frequência. |

**Constantes:** `SERIES_STEO`, `SERIES_PETROLEUM` — mapeamento setor × frequência → séries.

**Requisito:** `.env` com `TOKEN_EIA=...` (ou variável de ambiente), token obtido em [eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php).
