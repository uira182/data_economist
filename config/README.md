# Configuração e token PyPI

## Onde guardar o token do PyPI

O token **nunca** deve ser commitado no Git. Use uma destas opções:

### Opção 1: Ficheiro `.env` na raiz do projeto (recomendado)

1. Na raiz do projeto (`c:\BAU\data_economist\`), crie um ficheiro chamado **`.env`**.
2. Adicione (substitua pelo seu token real):

   ```
   TWINE_USERNAME=__token__
   TWINE_PASSWORD=pypi-xxxxxxxxxxxxxxxx
   ```

3. O `.env` já está no `.gitignore`, por isso não será enviado para o GitHub.

Para publicar usando as variáveis do `.env` no Windows (PowerShell):

```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^#][^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }
python -m twine upload dist/*
```

Ou use um pacote como `python-dotenv` num script de publicação que carregue o `.env` antes de chamar o twine.

### Opção 2: Variáveis de ambiente do sistema

No Windows, defina as variáveis de ambiente (uma vez):

- `TWINE_USERNAME` = `__token__`
- `TWINE_PASSWORD` = o seu token do PyPI

Assim o `twine upload` usa-as automaticamente e não precisa de ficheiro no projeto.

### Opção 3: Ficheiro `.pypirc` no seu utilizador

Crie ou edite `C:\Users\Uira\.pypirc` (não dentro do projeto):

```ini
[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxx
```

O ficheiro `.pypirc` não deve estar na pasta do projeto para não correr risco de ser commitado.

---

**Resumo:** O template está em `config/.env.example`. Copie os nomes das variáveis para um `.env` na raiz ou use variáveis de ambiente / `.pypirc` no utilizador. Nunca commite o token.
