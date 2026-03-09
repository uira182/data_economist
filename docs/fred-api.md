# Relatório: API FRED (Federal Reserve Bank of St. Louis)

## 1. Visão Geral

O FRED (Federal Reserve Economic Data) é o banco de dados econômico mantido pelo Federal Reserve Bank of St. Louis. Disponibiliza mais de **800.000 séries temporais** cobrindo indicadores macroeconômicos dos EUA e de outros países: inflação, emprego, câmbio, juros, PIB, produção industrial, mercado de capitais e muito mais.

- Site: https://fred.stlouisfed.org/
- API base: `https://api.stlouisfed.org/fred/`
- Documentação oficial: https://fred.stlouisfed.org/docs/api/fred/
- Registro de API key: https://fred.stlouisfed.org/docs/api/api_key.html

---

## 2. Autenticação

Toda requisição exige um parâmetro `api_key` (string de 32 caracteres hexadecimais).

- O token é **gratuito** e pode ser obtido em https://fred.stlouisfed.org/docs/api/api_key.html.
- No pacote `data_economist`, o token é lido da variável de ambiente `TOKEN_FRED` (arquivo `.env`).

**Exemplo de URL com token:**

```
https://api.stlouisfed.org/fred/series/observations
    ?series_id=CPIAUCSL
    &api_key=SEU_TOKEN
    &file_type=json
```

---

## 3. Formato de Resposta

Todas as respostas são em JSON (parâmetro `file_type=json`). Cada endpoint retorna um objeto com uma chave raiz diferente:

| Endpoint | Chave raiz no JSON |
|---|---|
| `/fred/series` | `seriess` (lista) |
| `/fred/series/observations` | `observations` (lista) |
| `/fred/series/search` | `seriess` (lista) |
| `/fred/category` | `categories` (lista) |
| `/fred/category/series` | `seriess` (lista) |
| `/fred/release` | `releases` (lista) |
| `/fred/release/series` | `seriess` (lista) |
| `/fred/tags/series` | `seriess` (lista) |

---

## 4. Endpoints Principais

### 4.1 Metadados de uma série — `/fred/series`

Retorna informações descritivas de uma série pelo seu `series_id`.

**URL:**
```
GET https://api.stlouisfed.org/fred/series
    ?series_id=CPIAUCSL
    &api_key=SEU_TOKEN
    &file_type=json
```

**Resposta (campo `seriess[0]`):**

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | str | Identificador único (ex.: `CPIAUCSL`) |
| `title` | str | Nome descritivo completo |
| `frequency` | str | Frequência textual (ex.: `Monthly`) |
| `frequency_short` | str | Frequência curta (ex.: `M`) |
| `units` | str | Unidade de medida |
| `units_short` | str | Unidade curta |
| `seasonal_adjustment` | str | Ajuste sazonal (ex.: `Seasonally Adjusted`) |
| `seasonal_adjustment_short` | str | Ajuste curto (ex.: `SA`) |
| `observation_start` | str | Data da primeira observação (`YYYY-MM-DD`) |
| `observation_end` | str | Data da última observação (`YYYY-MM-DD`) |
| `last_updated` | str | Última atualização no FRED |
| `realtime_start` | str | Início do período realtime |
| `realtime_end` | str | Fim do período realtime |
| `notes` | str | Notas metodológicas (pode estar ausente) |

---

### 4.2 Observações de uma série — `/fred/series/observations`

Retorna os valores históricos da série.

**URL:**
```
GET https://api.stlouisfed.org/fred/series/observations
    ?series_id=CPIAUCSL
    &api_key=SEU_TOKEN
    &file_type=json
    &observation_start=2010-01-01
    &observation_end=2024-12-31
```

**Parâmetros opcionais:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `observation_start` | str | Data inicial das observações (`YYYY-MM-DD`); padrão: início da série |
| `observation_end` | str | Data final das observações (`YYYY-MM-DD`); padrão: hoje |
| `realtime_start` | str | Início do período realtime (para dados vintage) |
| `realtime_end` | str | Fim do período realtime |
| `units` | str | Transformação: `lin` (nível), `chg` (variação), `pch` (%), `pc1` (% a/a), `log` (log) |
| `frequency` | str | Agregação: `d`, `w`, `bw`, `m`, `q`, `sa`, `a` |
| `aggregation_method` | str | Método de agregação: `avg`, `sum`, `eop` |
| `limit` | int | Número máximo de resultados (padrão: 100000) |
| `sort_order` | str | `asc` ou `desc` |

**Resposta (campo `observations`):**

```json
{
  "observations": [
    { "realtime_start": "2024-01-01", "realtime_end": "9999-12-31",
      "date": "2010-01-01", "value": "217.488" },
    ...
  ]
}
```

Cada observação tem:
- `date`: data (`YYYY-MM-DD`)
- `value`: valor como string (pode ser `"."` para missing/não divulgado)

**Observação importante:** séries como `SP500` retornam erro HTTP 400 quando os parâmetros `realtime_start`/`realtime_end` são passados. Nesse caso, a requisição deve ser feita sem esses campos.

---

### 4.3 Busca de séries — `/fred/series/search`

Busca séries pelo texto (nome, descrição, ID).

**URL:**
```
GET https://api.stlouisfed.org/fred/series/search
    ?search_text=consumer+price+index
    &api_key=SEU_TOKEN
    &file_type=json
    &limit=50
    &order_by=popularity
    &sort_order=desc
```

**Parâmetros relevantes:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `search_text` | str | Texto de busca (palavras separadas por `+` na URL) |
| `search_type` | str | `full_text` (padrão) ou `series_id` |
| `limit` | int | Número de resultados (máx. 1000) |
| `order_by` | str | `search_rank`, `series_id`, `title`, `units`, `frequency`, `seasonal_adjustment`, `realtime_start`, `realtime_end`, `last_updated`, `observation_start`, `observation_end`, `popularity` |
| `sort_order` | str | `asc` ou `desc` |
| `filter_variable` | str | Filtro por campo (ex.: `frequency`) |
| `filter_value` | str | Valor do filtro |
| `tag_names` | str | Tags separadas por `;` (ex.: `annual;cpi`) |

Retorna lista de objetos com a mesma estrutura de metadados do endpoint `/fred/series`.

---

### 4.4 Categoria — `/fred/category`

Retorna informação de uma categoria do FRED (estrutura hierárquica).

**URL:**
```
GET https://api.stlouisfed.org/fred/category
    ?category_id=125
    &api_key=SEU_TOKEN
    &file_type=json
```

A categoria raiz tem `category_id=0`. Cada categoria tem `id`, `name` e `parent_id`.

---

### 4.5 Séries de uma categoria — `/fred/category/series`

Lista as séries pertencentes a uma categoria.

**URL:**
```
GET https://api.stlouisfed.org/fred/category/series
    ?category_id=125
    &api_key=SEU_TOKEN
    &file_type=json
    &limit=100
```

---

### 4.6 Releases — `/fred/release` e `/fred/release/series`

Um **release** é uma publicação oficial (ex.: CPI da BLS, NFP). Cada série pertence a um release.

**URL (info do release):**
```
GET https://api.stlouisfed.org/fred/release
    ?release_id=10
    &api_key=SEU_TOKEN
    &file_type=json
```

**URL (séries do release):**
```
GET https://api.stlouisfed.org/fred/release/series
    ?release_id=10
    &api_key=SEU_TOKEN
    &file_type=json
    &limit=100
```

---

### 4.7 Tags — `/fred/tags/series`

Busca séries que têm determinadas tags.

**URL:**
```
GET https://api.stlouisfed.org/fred/tags/series
    ?tag_names=cpi;monthly
    &api_key=SEU_TOKEN
    &file_type=json
    &limit=50
```

---

## 5. Códigos de Erro HTTP

| Código | Significado |
|---|---|
| 200 | Sucesso |
| 400 | Parâmetros inválidos (ex.: `realtime_start/end` em séries que não aceitam) |
| 403 | API key inválida ou ausente |
| 404 | Série ou recurso não encontrado |
| 429 | Limite de requisições excedido |
| 500 | Erro interno do FRED |

**Atenção:** erros de autenticação com token inválido retornam status 200 com corpo `{"error_code": 400, "error_message": "Bad Request. Variable api_key is not one of the current api_keys."}`.

---

## 6. Séries de Referência do Notebook de Ingestão

### Diárias
| Série | Descrição |
|---|---|
| `DTWEXBGS` | US Dollar Index — amplo (Broad) |
| `DTWEXAFEGS` | US Dollar Index — economias avançadas |
| `DTWEXEMEGS` | US Dollar Index — emergentes |
| `VIXCLS` | VIX (volatilidade implícita S&P 500) |
| `SP500` | S&P 500 |
| `DEXCHUS` | Taxa de câmbio USD/CNY (China) |

### Mensais — Política Monetária
| Série | Descrição |
|---|---|
| `CPIAUCSL` | CPI — todos os itens, sazonalmente ajustado |
| `CPILFESL` | CPI — core (ex-alimentos e energia), SA |
| `CUSR0000SAS` | CPI — serviços, SA |
| `UNRATE` | Taxa de desemprego (%) |
| `DFEDTARU` | Federal Funds Rate — limite superior (target) |
| `DFEDTARL` | Federal Funds Rate — limite inferior (target) |
| `FEDFUNDS` | Federal Funds Effective Rate |
| `RTWEXBGS` | Real US Dollar Index — Broad |

### Mensais — Petróleo
| Série | Descrição |
|---|---|
| `WPU0543` | PPI — Petróleo bruto |
| `WPU0531` | PPI — Gás natural |

### Mensais — Mínério de Ferro e Siderurgia
| Série | Descrição |
|---|---|
| `WPU101707` | PPI — Lingotes de aço |
| `PPIACO` | PPI — todas as commodities |
| `WPU107601` | PPI — Fio-máquina de aço |
| `WPU1017` | PPI — Produtos ferrosos primários |
| `WPU03T15M05` | PPI — Minas e pedreiras |
| `PCU332618332618` | PPI — Arames e eletrodos |
| `PCU3312223312225` | PPI — Aço laminado plano |
| `WPU101704` | PPI — Placas e blocos de aço |

### Mensais — Bens de Capital
| Série | Descrição |
|---|---|
| `PCU33312033312011` | PPI — Turbinas a gás industriais |
| `PCU333131333131` | PPI — Bombas e compressores |
| `PCU3331313331319` | PPI — Compressores de ar |
| `PCU532412532412` | PPI — Aluguel de máquinas e equipamentos |
| `PCU336510336510541` | PPI — Aeronaves civis |
| `A33HNO` | Pedidos de bens de capital não-aeronaves |
| `WPU114908052` | PPI — Transformadores elétricos |
| `IPB50001N` | Produção industrial — bens de capital |

---

## 7. Fluxo de Requisição (Padrão do Notebook)

O notebook implementa dois passos:

1. **Busca de metadados** (`/fred/series`) para cada `series_id` — obtém `realtime_start`, `realtime_end`, `observation_start`, `observation_end`.
2. **Busca de observações** (`/fred/series/observations`) usando os campos de metadados para definir o intervalo.

Para séries marcadas como "especiais" (ex.: `SP500`), a chamada de observações omite `realtime_start`/`realtime_end` para evitar HTTP 400.

---

## 8. Limites e Boas Práticas

- Sem documentação formal de rate limiting, mas o FRED recomenda máximo de **1 request/segundo** para uso interativo.
- O parâmetro `limit` em observações tem padrão 100.000 (cobrindo séries longas).
- Valores `"."` na `value` representam observações faltantes ou não divulgadas — devem ser convertidos para `None` / `NaN`.
- O campo `realtime_end` com valor `"9999-12-31"` representa "sem fim definido" (dado vigente).
