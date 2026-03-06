# Fonte BCB SGS — Banco Central do Brasil

O módulo **bcb_sgs** do data_economist permite obter séries temporais do **Sistema Gerenciador de Séries Temporais (SGS)** do Banco Central do Brasil. A API exige intervalo por data (dataInicial e dataFinal) com **máximo de 10 anos** por requisição; o pacote faz várias requisições e monta um único JSON ordenado.

---

## Instalação e importação

```python
from data_economist import bcb_sgs
```

---

## API utilizada

| API | Base URL | Uso no pacote |
|-----|----------|----------------|
| **SGS (BCB)** | https://api.bcb.gov.br/dados/serie/bcdata.sgs | `bcb_sgs.get(codigo, date_init, date_end)` — séries por código e opcionalmente por intervalo de datas |

Documentação e dados abertos do BCB:
- [Portal de Dados Abertos do BCB](https://dadosabertos.bcb.gov.br)
- Endpoint de dados: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial=DD/MM/AAAA&dataFinal=DD/MM/AAAA`
- Endpoint último valor: `.../dados/ultimos/{N}?formato=json`

---

## bcb_sgs.get(codigo, date_init=None, date_end=None, timeout=30)

Obtém a série SGS para o **código** dado. As datas são opcionais e no formato **YYYY-MM-DD** (ex.: `"2020-01-01"`).

### Comportamento conforme os parâmetros

| Chamada | Comportamento |
|---------|----------------|
| `get(codigo)` | Obtém a data do último valor (`ultimos/1`) e volta de 10 em 10 anos até a API não retornar dados (404/5xx) ou ano &lt; 1950. |
| `get(codigo, "2020-01-01")` | Data mais recente via `ultimos/1`; volta de 10 em 10 anos **até** a data inicial; devolve de 2020-01-01 até o último valor. |
| `get(codigo, None, "2000-01-06")` | Usa **2000-01-06** como data final; volta de 10 em 10 anos para trás até não obter resultado. |
| `get(codigo, "2020-01-01", "2025-01-01")` | Intervalo fixo: requisita apenas [date_init, date_end] em janelas de 10 anos (não chama `ultimos/1`). |

### Parâmetros

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| **codigo** | `int` ou `str` | Código da série no SGS (ex.: 433 = IPCA). |
| **date_init** | `str` ou `datetime` ou `None` | Data inicial no formato `YYYY-MM-DD`. Opcional. |
| **date_end** | `str` ou `datetime` ou `None` | Data final no formato `YYYY-MM-DD`. Opcional. |
| **timeout** | `int` | Timeout em segundos por requisição (default 30). |

### Retorno

- **Retorno:** `list[dict]` — cada elemento tem `"data"` (DD/MM/YYYY) e `"valor"` (string), ordenado da data mais antiga para a mais recente.
- **Erros:** `requests.HTTPError` em falha HTTP; `ValueError` se a série não existir ou a resposta for inválida. Em 404 ou 5xx numa janela intermediária, o pacote para e devolve os dados já obtidos.

### Exemplos

**Série completa (último valor até onde houver dados):**

```python
from data_economist import bcb_sgs

dados = bcb_sgs.get(433)   # IPCA
# dados[0]["data"], dados[0]["valor"]; lista em ordem cronológica
```

**Do início de 2020 até o último valor:**

```python
dados = bcb_sgs.get(433, "2020-01-01")
```

**Da data final para trás (sem data inicial):**

```python
dados = bcb_sgs.get(433, None, "2000-01-06")  # de 2000-01-06 para trás, 10 em 10 anos
```

**Intervalo fixo:**

```python
dados = bcb_sgs.get(433, "2020-01-01", "2025-01-01")  # só 2020–2025
```

**Converter para pandas:**

```python
import pandas as pd

dados = bcb_sgs.get(433, "2020-01-01", "2025-01-01")
df = pd.DataFrame(dados)
df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
df["valor"] = df["valor"].astype(float)
```

---

## Códigos de série (exemplos)

Alguns códigos SGS muito usados (consulte o portal do BCB para a lista completa):

| Código | Descrição |
|--------|-----------|
| 433 | IPCA (Índice Nacional de Preços ao Consumidor Amplo) |
| 12 | Taxa de juros - Selic |
| 432 | IGP-DI (Índice Geral de Preços - Disponibilidade Interna) |

O BCB disponibiliza listagens e metadados das séries no [Portal de Dados Abertos](https://dadosabertos.bcb.gov.br).
