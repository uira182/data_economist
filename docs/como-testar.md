# Como testar o projeto (Python + pytest)

Este projeto usa **pytest** para testes. As dependências de teste estão em `pyproject.toml` (opção `dev`).

---

## 1. Extensões no Cursor / VS Code

Recomendadas para testes em Python:

| Extensão | ID | O que faz |
|----------|-----|-----------|
| **Python** | `ms-python.python` | Interpretador, execução de ficheiros, **descoberta e execução de testes** (pytest incluído). |
| **Pytest** | `littlefoxteam.vscode-pytest-test-adapter` | Painel lateral com lista de testes, botão "Run" por teste ou ficheiro, integração com o editor. |

### Como instalar no Cursor

1. Abra a paleta: `Ctrl+Shift+P` (ou `Cmd+Shift+P` no Mac).
2. Escreva **Extensions: Install Extensions**.
3. Pesquise **Python** e instale a da Microsoft.
4. (Opcional) Pesquise **Pytest** e instale **Pytest** (por Little Fox Team) ou use só a integração de testes da extensão Python.

Depois de instalar a extensão **Python**, o Cursor passa a detectar os testes: aparece "Run Test" / "Debug Test" por cima de cada `def test_...` e um ícone de play no painel lateral em **Testing**.

---

## 2. Preparar o ambiente

Na raiz do projeto (`c:\BAU\data_economist`):

```powershell
# Instalar o pacote em modo editável + dependências de teste
pip install -e ".[dev]"
```

Assim o `data_economist` fica importável e o pytest disponível.

---

## 3. Rodar os testes

### No terminal

```powershell
# Todos os testes
python -m pytest

# Com mais detalhe
python -m pytest -v

# Só a pasta tests/
python -m pytest tests/

# Um ficheiro
python -m pytest tests/test_sidra.py

# Um teste específico (pelo nome)
python -m pytest tests/test_sidra.py::test_get_retorna_lista
```

### No Cursor / VS Code

- **Painel Testing:** Abra o ícone de “flask”/testes na barra lateral. Os testes aparecem listados; clique no play ao lado de um teste ou de uma pasta para executar.
- **Por cima do teste:** Abra um ficheiro como `tests/test_sidra.py`; por cima de cada `def test_...` aparece **Run Test** | **Debug Test**. Clique para rodar só aquele teste.
- **Paleta:** `Ctrl+Shift+P` → **Testing: Run All Tests** (ou **Run Last Test**).

---

## 4. Estrutura dos testes neste projeto

- **`tests/test_package.py`** — testes gerais do pacote (import, versão).
- **`tests/test_sidra.py`** — testes da função `get` da API SIDRA.
- **`tests/testar_instalacao.ipynb`** — notebook com as 4 etapas de instalação (não é pytest).

Os testes que chamam a API real (por exemplo SIDRA) fazem pedidos à internet; se quiser testes mais rápidos ou offline, pode usar mocks (ex.: `pytest` + `responses` ou `unittest.mock`).

---

## 5. Resumo rápido

| O que quero | Comando / ação |
|-------------|-----------------|
| Rodar todos os testes | `python -m pytest` ou painel Testing → Run All |
| Rodar um ficheiro | `python -m pytest tests/test_sidra.py` |
| Rodar um teste | Botão "Run Test" em cima do `def test_...` ou `python -m pytest tests/test_sidra.py::test_get_retorna_lista` |
| Ver output detalhado | `python -m pytest -v` |

Com a extensão **Python** (e opcionalmente **Pytest**) instalada, o Cursor passa a mostrar os testes na barra lateral e a permitir executá-los com um clique.
