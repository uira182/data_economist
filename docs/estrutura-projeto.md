# Estrutura do projeto recomendada

Esta página descreve a estrutura de pastas e ficheiros recomendada para o **data_economist**, de forma a ser fácil de desenvolver, testar e publicar como pacote público.

---

## Visão geral

```
data_economist/                    # Raiz do repositório
├── src/
│   └── data_economist/            # Código do pacote (o que vai no PyPI)
│       ├── __init__.py            # Expõe a API pública
│       └── fontes/                # Módulos por fonte (BCE, Eurostat, IMF...)
│           └── __init__.py
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
"""data_economist: funções para baixar dados de fontes económicas."""

__version__ = "0.1.0"

from data_economist.bce import baixar_taxas_bce
from data_economist.eurostat import baixar_indicador_eurostat

__all__ = [
    "baixar_taxas_bce",
    "baixar_indicador_eurostat",
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

## Organização por fonte económica

Pode organizar as funções por fonte (BCE, Eurostat, IMF, etc.) em módulos separados:

- `data_economist/bce.py` — funções que usam APIs/dados do BCE
- `data_economist/eurostat.py` — Eurostat
- `data_economist/imf.py` — IMF

Cada módulo pode ter várias funções (por série, por indicador, etc.). No `__init__.py` importe e liste em `__all__` apenas as funções que considera estáveis e públicas.

---

## Ficheiros que não entram no pacote

Por defeito, o setuptools (com `pyproject.toml`) inclui o que está em `src/data_economist/`. Ficheiros como:

- `docs/`
- `tests/`
- `README.md`, `LICENSE`, `.gitignore`

não são instalados como módulos Python, mas fazem parte do repositório e são importantes para documentação, testes e publicação (o README é mostrado no PyPI).

Esta estrutura facilita a criação de um dicionário/pacote público: o código fica em `src/data_economist/`, a documentação em `docs/`, e o resto é suporte à publicação e à comunidade.
