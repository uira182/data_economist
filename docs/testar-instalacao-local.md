# Testar a instalação do pacote no seu computador

Antes de publicar no PyPI, pode testar exatamente o que os utilizadores vão receber ao instalar o pacote.

---

## Opção 1: Instalar a partir do ficheiro construído (recomendado para “teste final”)

Simula a instalação real (como `pip install data-economist` no PyPI).

### 1. Construir o pacote

Na raiz do projeto (`c:\BAU\data_economist`):

```powershell
python -m build
```

Isto gera a pasta `dist/` com um ficheiro `.whl` e um `.tar.gz`.

### 2. (Opcional) Criar um ambiente virtual só para o teste

```powershell
python -m venv .venv_test
.venv_test\Scripts\activate
```

### 3. Instalar o pacote a partir do `.whl`

```powershell
pip install dist\data_economist-0.1.0-py3-none-any.whl
```

(Substitua `0.1.0` pela versão que está no seu `pyproject.toml` se for diferente.)

### 4. Testar no Python

```powershell
python -c "import data_economist; print(data_economist.__version__)"
```

Se imprimir a versão (ex.: `0.1.0`), a instalação local funcionou como para um utilizador final.

### 5. Desinstalar depois do teste

```powershell
pip uninstall data-economist -y
```

Se usou `.venv_test`, pode apagar a pasta quando não precisar mais.

---

## Opção 2: Modo editável (desenvolvimento)

Útil enquanto desenvolve: as alterações no código reflectem-se logo ao importar.

Na raiz do projeto:

```powershell
pip install -e .
```

Depois pode fazer `import data_economist` em qualquer script; ao editar ficheiros em `src/data_economist/`, não precisa de reinstalar. Para “testar como utilizador”, use a Opção 1.

---

## Resumo

| Objetivo | Comando |
|----------|--------|
| Construir o pacote | `python -m build` |
| Instalar como utilizador (teste local) | `pip install dist\data_economist-0.1.0-py3-none-any.whl` |
| Verificar | `python -c "import data_economist; print(data_economist.__version__)"` |
| Desinstalar | `pip uninstall data-economist -y` |

Depois de confirmar que tudo funciona assim no seu PC, pode publicar no PyPI com confiança.
