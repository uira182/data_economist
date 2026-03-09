# Estrutura do projeto recomendada

Esta página descreve a estrutura de pastas e ficheiros recomendada para o **data_economist**, de forma a ser fácil de desenvolver, testar e publicar como pacote público.

---

## Visão geral

```
data_economist/                    # Raiz do repositório
├── src/
│   └── data_economist/            # Código do pacote (o que vai no PyPI)
│       ├── __init__.py            # Expõe a API pública (ibge, bcb_sgs)
│       ├── ibge.py                # IBGE SIDRA e metadados
│       ├── bcb_sgs.py             # Banco Central — SGS (séries temporais)
│       └── fontes/                 # Módulos por fonte
│           ├── __init__.py
│           └── sidra.py            # Reexporta ibge
├── docs/                          # Documentação (como esta)
│   ├── README.md
│   ├── guia-publicacao-pacote.md
│   ├── estrutura-projeto.md
│   └── uso-pelo-utilizador.md
├── config/                        # Configuração (exemplo .env para token PyPI)
│   ├── .env.example
│   └── README.md
├── scripts/                       # Scripts auxiliares (ex.: upload_pypi.py)
├── tests/
│   ├── __init__.py
│   └── test_package.py
├── pyproject.toml                 # Configuração do pacote (nome, versão, deps)
├── README.md                      # Mostrado no PyPI e no repositório
├── LICENSE
└── .gitignore
```

---

## Papel de cada parte

| Pasta/ficheiro | Função |
|----------------|--------|
| **src/data_economist/** | Todo o código que os utilizadores importam (`import data_economist`). Aqui ficam as funções para baixar dados económicos. |
| **docs/** | Guias e documentação para quem desenvolve e para quem usa o pacote. |
| **tests/** | Testes (ex.: pytest). Não são instalados com o pacote, mas são essenciais para qualidade. |
| **pyproject.toml** | Define nome do pacote, versão, dependências e como construir o pacote para publicação. |
| **README.md** | Primeira impressão no PyPI e no repositório: instalação, exemplos e links. |
| **LICENSE** | Licença de uso (ex.: MIT) para a comunidade poder usar e redistribuir. |

---

## API pública em `__init__.py`

No `src/data_economist/__init__.py` convém expor as funções que quer que a comunidade use diretamente, por exemplo:

```python
# src/data_economist/__init__.py
"""data_economist: fontes de dados (IBGE, BCB, ComexStat, EIA) e funcionalidades (ex.: dessazonalização X-13)."""

__version__ = "0.5.0"

from data_economist import ibge, bcb_sgs, comexstat, eia, x13

__all__ = [
    "ibge",
    "bcb_sgs",
    "comexstat",
    "eia",
    "x13",
    "__version__",
]
```

Assim, o utilizador pode fazer:

```python
import data_economist

data_economist.baixar_taxas_bce(...)
# ou
from data_economist import baixar_taxas_bce
```

---

## Organização: fontes de dados e funcionalidades

**Fontes de dados** (obter dados de APIs públicas):

- **`data_economist/ibge.py`** — API SIDRA e API de Agregados do IBGE: `get()`, `url()`, `metadados()`. Ver [Fonte IBGE](fonte-ibge.md).
- **`data_economist/bcb_sgs.py`** — Séries temporais do Banco Central (SGS): `get(codigo, date_init, date_end)`. Ver [Fonte BCB SGS](fonte-bcb-sgs.md).
- **`data_economist/comexstat.py`** — ComexStat (MDIC). Ver [Fonte ComexStat](fonte-comexstat.md).
- **`data_economist/eia.py`** — EIA (dados energéticos). Ver [Fonte EIA](fonte-eia.md).
- **`data_economist/fontes/sidra.py`** — Reexporta funções do ibge para uso por fonte.

**Funcionalidades** (análise/processamento, não fontes):

- **`data_economist/x13/`** — Dessazonalização X-13ARIMA-SEATS: `seas()`, `final()`, `trend()`, etc. Ver [Dessazonalização X-13](fonte-x13.md).
- **`data_economist/tratamento/`** — Filtros (HP, BK, CF), suavização exponencial (SES, DES, Holt, Holt-Winters, ETS), conversão de frequência e whitening AR(p). Ver [Tratamento de séries](fonte-tratamento.md).
- **`data_economist/estatistica/`** — Estatística descritiva, normalidade, correlação, testes de hipótese, contingência, PCA e análise fatorial. Ver [Estatística](fonte-estatistica.md).

Outras fontes (BCE, Eurostat, IMF) podem ser adicionadas em módulos separados. No `__init__.py` importe e liste em `__all__` os módulos e funções estáveis e públicas.

---

## Ficheiros que não entram no pacote

Por defeito, o setuptools (com `pyproject.toml`) inclui o que está em `src/data_economist/`. Ficheiros como:

- `docs/`
- `tests/`
- `README.md`, `LICENSE`, `.gitignore`

não são instalados como módulos Python, mas fazem parte do repositório e são importantes para documentação, testes e publicação (o README é mostrado no PyPI).

Esta estrutura facilita a criação de um dicionário/pacote público: o código fica em `src/data_economist/`, a documentação em `docs/`, e o resto é suporte à publicação e à comunidade.
