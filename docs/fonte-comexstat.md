# Fonte ComexStat — MDIC (comércio exterior)

O módulo **comexstat** do data_economist permite obter dados de comércio exterior do **ComexStat** (Ministério do Desenvolvimento, Indústria, Comércio e Serviços). Inclui: consulta por body (POST), consulta por mapeamentos (GET /general) e uso de **filtros guardados** no site (por ID ou URL).

---

## Instalação e importação

```python
from data_economist import comexstat
```

---

## APIs utilizadas

| API | Base URL | Uso no pacote |
|-----|----------|---------------|
| **Historical data** | https://api-comexstat.mdic.gov.br/historical-data | `comexstat.get(body)` — POST com body no padrão oficial |
| **General** | https://api-comexstat.mdic.gov.br/general | `comexstat.get_general(...)` e `comexstat.get_by_filter(id ou url)` |
| **Filter** | https://api-comexstat.mdic.gov.br/filter | `comexstat.get_filter(id)` — obtém filtro guardado |

Documentação oficial da API: [ComexStat MDIC](https://api-comexstat.mdic.gov.br/docs).  
Portal: [comexstat.mdic.gov.br](https://comexstat.mdic.gov.br).

---

## comexstat.get(body, timeout=120)

Consulta dados históricos via **POST /historical-data**. O **body** deve seguir o padrão da documentação oficial da API.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **body** | `dict` | Payload: `flow`, `monthDetail`, `period`, `filters`, `details`, `metrics` (ver documentação oficial). |
| **timeout** | `int` | Timeout em segundos (default 120). |

### Retorno

- **Retorno:** `dict` ou `list` — resposta da API (em geral `{"data": ..., "success": ...}`).
- **Erros:** `requests.HTTPError` em falha HTTP.

### Exemplo

```python
from data_economist import comexstat

body = {
    "flow": "export",
    "monthDetail": False,
    "period": {"from": "2018-01", "to": "2018-01"},
    "filters": [{"filter": "state", "values": [26]}],
    "details": ["country", "state"],
    "metrics": ["metricFOB", "metricKG"],
}
resultado = comexstat.get(body)
# resultado["data"], resultado["success"], etc.
```

---

## comexstat.get_general(flow, filter_key, filter_values, metrics, timeout=120)

Consulta dados via **GET /general** usando mapeamentos internos (ex.: CUCI Grupo, posição SH4). Útil para consultas por produto (cuciGroup, chapter4) sem montar o body manualmente.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **flow** | `str` | `"export"` ou `"import"`. |
| **filter_key** | `str` | Chave do filtro: `"cuciGroup"` (CUCI Grupo) ou `"chapter4"` (posição SH4). |
| **filter_values** | `list[str]` | Valores do filtro (ex.: `["281b"]` para minério de ferro, `["2603"]` para minério de cobre). |
| **metrics** | `str` ou `list[str]` | Métrica(s): `"metricFOB"`, `"metricKG"`, etc. |
| **timeout** | `int` | Timeout em segundos (default 120). |

### Retorno

- **Retorno:** `dict` — resposta de GET /general; os registos ficam em **`resultado["data"]["list"]`**.
- **Erros:** `requests.HTTPError` em falha HTTP.

### Exemplos

**Exportações por CUCI Grupo (ex.: 281b — minério de ferro), valor FOB:**

```python
from data_economist import comexstat

dados = comexstat.get_general("export", "cuciGroup", ["281b"], "metricFOB")
registos = dados["data"]["list"]
# Cada item: campos conforme a API (país, valor, etc.)
```

**Importações por posição SH4 (ex.: 2603 — minério de cobre), peso em kg:**

```python
dados = comexstat.get_general("import", "chapter4", ["2603"], "metricKG")
lista = dados["data"]["list"]
```

---

## comexstat.get_filter(filter_id, timeout=30)

Obtém um **filtro guardado** no site ComexStat (quando o utilizador cria um filtro na página "geral" e partilha ou guarda o link). Faz **GET /filter/{id}**.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **filter_id** | `str` ou `int` | ID do filtro (ex.: `146862`) ou URL completa (ex.: `https://comexstat.mdic.gov.br/pt/geral/146862`). Se for URL, o ID é extraído automaticamente. |
| **timeout** | `int` | Timeout em segundos (default 30). |

### Retorno

- **Retorno:** `dict` — resposta da API com `data.id`, `data.filter` (string JSON com o payload para /general) e `data.createdAt`.
- **Erros:** `requests.HTTPError` em falha HTTP.

### Exemplo

```python
from data_economist import comexstat

# Por ID
resp = comexstat.get_filter(146862)
# resp["data"]["id"] == 146862
# resp["data"]["filter"] — string JSON
# resp["data"]["createdAt"]

# Por URL (extrai o ID)
resp = comexstat.get_filter("https://comexstat.mdic.gov.br/pt/geral/146862")
```

---

## comexstat.get_by_filter(filter_id_or_url, timeout=120)

Obtém os **dados** usando um filtro guardado no site: primeiro chama **GET /filter/{id}** para obter o payload, depois **GET /general** com esse payload. Aceita o **ID** (número) ou a **URL** da página (ex.: `.../geral/146862`).

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **filter_id_or_url** | `str` ou `int` | ID do filtro (ex.: `146862`) ou URL (ex.: `https://comexstat.mdic.gov.br/pt/geral/146862`). |
| **timeout** | `int` | Timeout em segundos para cada requisição (default 120). |

### Retorno

- **Retorno:** `dict` — mesma estrutura que GET /general; os registos ficam em **`resultado["data"]["list"]`**.
- **Erros:** `requests.HTTPError` em falha HTTP; `ValueError` se a resposta do /filter não contiver `data.filter`.

### Exemplos

**Por ID (número):**

```python
from data_economist import comexstat

dados = comexstat.get_by_filter(146862)
registos = dados["data"]["list"]
```

**Por URL da página (o pacote extrai o ID após `/geral/` ou `/general/`):**

```python
dados = comexstat.get_by_filter("https://comexstat.mdic.gov.br/pt/geral/146862")
registos = dados["data"]["list"]
```

---

## Resumo das funções

| Função | Uso principal |
|--------|----------------|
| `get(body)` | POST /historical-data — body no padrão da documentação oficial. |
| `get_general(flow, filter_key, filter_values, metrics)` | GET /general — consultas por CUCI Grupo ou posição SH4 com mapeamentos internos. |
| `get_filter(filter_id)` | GET /filter/{id} — obter definição de um filtro guardado no site. |
| `get_by_filter(filter_id_or_url)` | Obter dados usando um filtro guardado (ID ou URL da página geral). |

---

## Plano e referências

- Plano de integração e detalhes técnicos: [docs/planos/plano-comexstat.md](planos/plano-comexstat.md).
- Testes e exemplos de uso: `tests/test_comexstat.py`, `tests/usar_pacote_instalado.py`.
