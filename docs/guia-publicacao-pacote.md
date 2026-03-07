# Guia: Como criar e publicar um pacote Python público

Este guia explica como transformar o **data_economist** num pacote Python que qualquer pessoa pode instalar com `pip install data-economist` e usar as suas funções.

---

## 1. O que é um "pacote público" em Python?

- Um **pacote** é uma pasta com código Python (módulos) que pode ser importado.
- **Público** significa que está publicado num repositório (por exemplo **PyPI** — Python Package Index), de onde os utilizadores fazem `pip install nome-do-pacote`.

Assim, a comunidade pode usar as suas funções de dados económicos sem copiar código: basta instalar o pacote.

---

## 2. Passos para publicar o pacote

### 2.1 Estrutura mínima do projeto

O projeto deve ter uma estrutura como esta (detalhes em [Estrutura do projeto](estrutura-projeto.md)):

```
data_economist/
├── src/
│   └── data_economist/
│       ├── __init__.py
│       ├── fontes/           # módulos por fonte (BCE, Eurostat, etc.)
│       │   └── ...
│       └── ...
├── docs/
├── tests/
├── pyproject.toml           # configuração moderna do pacote
├── README.md
└── LICENSE
```

- O código do pacote fica dentro de `src/data_economist/`.
- `pyproject.toml` define nome, versão, dependências e como construir o pacote.

### 2.2 Ficheiro `pyproject.toml`

Este ficheiro diz ao Python e ao `pip` como tratar o seu projeto como pacote instalável. Exemplo:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "data-economist"
version = "0.1.0"
description = "Obter dados de fontes públicas (IBGE, BCB, ComexStat, EIA) e funcionalidades como dessazonalização (X-13)."
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Seu Nome", email = "seu@email.com"}]
keywords = ["economics", "data", "BCE", "Eurostat", "IMF"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.9"
dependencies = [
    "pandas>=1.3.0",
    "requests>=2.26.0",
]

[project.optional-dependencies]
dev = ["pytest", "black", "ruff"]

[project.urls]
Homepage = "https://github.com/seu-usuario/data_economist"
Documentation = "https://github.com/seu-usuario/data_economist#readme"
Repository = "https://github.com/seu-usuario/data_economist"

[tool.setuptools.packages.find]
where = ["src"]
```

- **name**: o nome que aparece no PyPI e no `pip install data-economist`.
- **version**: deve ser atualizado a cada release.
- **dependencies**: bibliotecas que o utilizador precisa para usar as suas funções.

### 2.3 Publicar no PyPI (Test PyPI e PyPI)

1. **Criar conta**
   - Test PyPI (para testes): https://test.pypi.org/account/register/
   - PyPI (produção): https://pypi.org/account/register/

2. **Criar token de API** (em PyPI: Account → API tokens) com permissão para publicar projetos.  
   **Onde guardar o token:** use um ficheiro `.env` na raiz do projeto (ver [config/README.md](../config/README.md)) ou variáveis de ambiente. Nunca commite o token no Git.

3. **Instalar ferramentas de publicação**
   ```bash
   pip install build twine
   ```

4. **Construir o pacote**
   ```bash
   cd c:\BAU\data_economist
   python -m build
   ```
   Isto gera ficheiros em `dist/` (por exemplo `.whl` e `.tar.gz`).

5. **Publicar no Test PyPI (recomendado primeiro)**
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```
   Quando pedido, use o token de API do Test PyPI.

6. **Testar instalação a partir do Test PyPI**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ data-economist
   ```

7. **Publicar no PyPI (produção)**
   ```bash
   python -m twine upload dist/*
   ```
   Depois disso, qualquer pessoa pode fazer:
   ```bash
   pip install data-economist
   ```

### 2.4 Versionamento

- Use **versionamento semântico**: `MAJOR.MINOR.PATCH` (ex.: `0.1.0`, `1.0.0`).
- Atualize a versão em `pyproject.toml` (e se tiver `setup.py`/`setup.cfg`) antes de cada upload.
- Não reutilize a mesma versão no PyPI; para corrigir, suba uma nova versão.

---

## 3. Manter o pacote útil para a comunidade

- **README.md**: instruções de instalação, exemplos de uso e links para documentação.
- **docs/**: guias (como este) e referência das funções.
- **LICENSE**: escolha uma licença aberta (MIT, Apache 2.0, etc.) para que outros possam usar e contribuir.
- **Changelog**: ficheiro (ex.: `CHANGELOG.md`) com as alterações por versão.
- **Issue tracker e contribuição**: no GitHub/GitLab, explique como reportar bugs e como contribuir (ex.: em `CONTRIBUTING.md`).

Quando o pacote estiver no PyPI e o README e a documentação estiverem claros, a comunidade pode descobrir o pacote, instalar com `pip install data-economist` e usar as funções que disponibilizar — conforme descrito em [Uso pelo utilizador](uso-pelo-utilizador.md).
