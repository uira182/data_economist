# Antes do commit e do push para o GitHub

## O que **não** deve ser commitado (já está no .gitignore)

| Item | Motivo |
|------|--------|
| **.env** | Contém token do PyPI (TWINE_PASSWORD). Nunca subir. |
| **.env.local**, **.env.*.local** | Variantes locais com segredos. |
| **config/secrets.*** | Ficheiros de segredos na pasta config. |
| ***.pypirc** | Credenciais do PyPI. |
| **__pycache__/**, **.pytest_cache/** | Cache do Python/pytest. |
| **build/**, **dist/**, ***.egg-info/** | Artefactos de build (gerados ao fazer `python -m build`). |
| **.venv/**, **venv/** | Ambientes virtuais. |
| **.ipynb_checkpoints/** | Checkpoints dos notebooks. |
| **.idea/**, **.vscode/** | Configurações de IDE (opcional manter; estão ignoradas). |

O ficheiro **config/.env.example** é só um modelo (sem token real) e **pode** ser commitado.

## Verificação rápida antes do primeiro push

1. Confirmar que **.env** não está tracked:  
   `git status` não deve listar `.env`.
2. Se já tiver feito `git add .` antes de criar o .gitignore:  
   `git rm --cached .env` (se aparecer), depois commit.
3. Depois do push, no GitHub não devem existir ficheiros com “token”, “password” ou “pypi-” em conteúdo sensível.

## Depois do push: publicar no PyPI

1. Na raiz: `python -m build`
2. Upload: `python -m twine upload dist/*` (usar token em variável de ambiente ou .env, nunca no código).
3. Ver [guia-publicacao-pacote.md](guia-publicacao-pacote.md) e [config/README.md](../config/README.md).
