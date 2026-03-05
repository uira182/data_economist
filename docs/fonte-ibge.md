# Fonte IBGE — Instituto Brasileiro de Geografia e Estatística

O módulo **ibge** do data_economist permite consultar dados e metadados do IBGE de forma direta, usando a API SIDRA (Sistema IBGE de Recuperação Automática) e a API de Agregados.

---

## Instalação e importação

```python
from data_economist import ibge
```

---

## APIs utilizadas

| API | Base URL | Uso no pacote |
|-----|----------|----------------|
| **SIDRA (values)** | https://apisidra.ibge.gov.br | `ibge.get(t, n, v, p, c)` — por parâmetros; `ibge.url(url)` — por URL(s) |
| **Agregados (metadados)** | https://servicodados.ibge.gov.br/api/v3/agregados | `ibge.metadados(tabela)` — metadados por número da tabela |

Documentação oficial do IBGE:
- [API SIDRA](https://apisidra.ibge.gov.br)
- [SIDRA no portal](https://sidra.ibge.gov.br)

---

## ibge.get(t, n, v, p, c)

Monta a URL da API SIDRA a partir dos parâmetros e devolve o resultado em JSON. Útil quando já se sabe a tabela, região, variável, período e classificação.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **t** | `int` ou `str` | Tabela (ex.: 8888). |
| **n** | `tuple (nível, valor)` ou `None` | Região: ex. `(3, "all")` → n3/all (UF, todos). |
| **v** | `int` ou `str` ou `None` | Variável (ex.: 12606). |
| **p** | `str` ou `None` | Período: `"all"`, `"first"`, `"last"` ou código. |
| **c** | `tuple (id_class, id_cat)` ou lista de tuples, ou `None` | Classificação: ex. `(544, 129317)`. |
| **d** | `str` ou `None` | Formato decimal (opcional). |

### Retorno e erros

- **Retorno:** `list` ou `dict` (JSON). Em erro HTTP (ex.: parâmetros inválidos), levanta `requests.HTTPError`.

### Exemplo

```python
# Combinação completa (equivalente a .../t/8888/n3/all/v/12606/p/first/c544/129317)
dados = ibge.get(t=8888, n=(3, "all"), v=12606, p="first", c=(544, 129317))
```

---

## ibge.url(url ou [url, url, ...])

Consulta **uma URL** ou **várias URLs** da API IBGE (em particular da SIDRA), identifica automaticamente o formato da resposta e devolve os dados em JSON.

- **Uma URL (str):** devolve o resultado dessa consulta (lista ou dict).
- **Várias URLs (list):** devolve uma **lista de resultados na mesma ordem**, formando um único JSON aninhado: `[resultado_url1, resultado_url2, ...]`.

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **url_or_urls** | `str` ou `list[str]` | Uma URL completa da consulta ou uma lista de URLs (ex.: `[url1, url2]`). |

Cada URL pode ser passada **com** ou **sem** `formato=json`; para URLs da SIDRA, o pacote pede JSON automaticamente se o parâmetro não existir.

### Retorno

- **Uma URL:** `list` ou `dict` (sempre serializável com `json.dumps()`).
- **Várias URLs:** `list` onde cada elemento é o resultado da URL na mesma posição (um único JSON aninhado).
- Na SIDRA, o primeiro elemento de cada lista costuma ser o **cabeçalho** (nomes das colunas); os seguintes são os **registos** (dados).

### Colunas no padrão SIDRA (dimensões D1 a D9)

A API SIDRA usa **dimensões** identificadas por colunas:

- **D1C, D1N, D2C, D2N, … até D9C, D9N** — cada dimensão tem código (sufixo **C**) e nome (sufixo **N**). O número (1 a 9) varia conforme a tabela.
- **Colunas fixas:** NC, NN (nível territorial), MC, MN (unidade de medida), **V** (valor).

Constantes disponíveis no módulo para referência: `ibge.COLUNAS_DIMENSAO_CODIGO`, `ibge.COLUNAS_DIMENSAO_NOME`, `ibge.DIMENSOES_SIDRA`.

### Exemplos

**Uma URL:**

```python
from data_economist import ibge

url = (
    "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/last/"
    "c544/129317/d/v12606%205"
)
dados = ibge.url(url)
# dados[0] = cabeçalho; dados[1:] = registos
import pandas as pd
df = pd.DataFrame(dados[1:])
```

**Várias URLs (resultados aninhados num único JSON):**

```python
dados_multi = ibge.url([url1, url2])
# dados_multi = [resultado_url1, resultado_url2], mesma ordem das URLs
```

### Erros

- **requests.HTTPError** — se a resposta HTTP indicar erro (ex.: 404, 500).

---

## ibge.metadados(tabela)

Obtém os **metadados** de uma tabela do IBGE (agregados/SIDRA) pelo número da tabela.

**URL utilizada:** `https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados`

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **tabela** | `int` ou `str` | Número da tabela (ex.: 8888 para Produção Física Industrial — PIMPF). |

### Retorno

- **Tipo:** `dict` com, entre outros:
  - **id** — número da tabela
  - **nome** — nome da tabela
  - **URL** — link para a tabela no portal SIDRA
  - **pesquisa** — nome da pesquisa
  - **assunto** — assunto (ex.: Indústria)
  - **periodicidade** — `frequencia`, `inicio`, `fim`
  - **nivelTerritorial** — níveis disponíveis (Administrativo, etc.)
  - **variaveis** — lista de variáveis (id, nome, unidade, sumarizacao)
  - **classificacoes** — classificações e categorias (ex.: CNAE)

### Exemplo

```python
from data_economist import ibge

meta = ibge.metadados(8888)
print(meta["nome"])           # Produção Física Industrial, por seções e atividades industriais
print(meta["periodicidade"])   # {"frequencia": "mensal", "inicio": 200201, "fim": 202512}
print(meta["variaveis"][0])    # primeira variável (id, nome, unidade)
```

### Erros

- **requests.HTTPError** — se a resposta HTTP indicar erro (ex.: tabela inexistente).

---

## Resumo rápido

| Função | Uso |
|--------|-----|
| `ibge.get(t, n, v, p, c)` | Dados SIDRA montando URL a partir dos parâmetros; retorno em JSON. |
| `ibge.url(url)` | Dados de uma URL SIDRA/IBGE; retorno em JSON (lista/dict). |
| `ibge.url([url, url, ...])` | Várias URLs; retorno em JSON aninhado: lista de resultados na mesma ordem. |
| `ibge.metadados(tabela)` | Metadados da tabela (id, nome, variaveis, classificacoes, etc.). |

---

## Testes no repositório

- **Testes unitários:** `tests/test_sidra.py` (pytest).
- **Notebooks de teste:** `tests/testar_get_sidra.ipynb` (url), `tests/testar_ibge_get.ipynb` (get com parâmetros e tratamento de erros), `tests/testar_metadados.ipynb` (metadados).
