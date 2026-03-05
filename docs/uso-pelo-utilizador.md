# Como os utilizadores instalam e usam o pacote

Este documento descreve, do ponto de vista de **quem vai usar** o data_economist, como instalar o pacote e como utilizar as funções que você disponibilizar. Pode usar este texto como base para a secção "Uso" do README ou da documentação pública.

---

## Instalação

Depois do pacote estar publicado no PyPI, qualquer pessoa pode instalar com:

```bash
pip install data-economist
```

Em ambientes virtuais (recomendado):

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
# ou: source .venv/bin/activate  # Linux/macOS
pip install data-economist
```

---

## Uso básico

Após a instalação, o utilizador importa o pacote e chama as funções que você expôs na API pública (em `__init__.py`).

### Exemplo 1: importar o módulo

```python
import data_economist

# Usar funções expostas no __init__.py
df = data_economist.baixar_taxas_bce("EST.BDE.STR")
```

### Exemplo 2: importar funções específicas

```python
from data_economist import baixar_taxas_bce, baixar_indicador_eurostat

df_bce = baixar_taxas_bce("EST.BDE.STR")
df_euro = baixar_indicador_eurostat("nama_10_gdp")
```

### Exemplo 3: verificar versão

```python
import data_economist

print(data_economist.__version__)
```

---

## O que você precisa garantir

Para que a comunidade use o pacote sem dificuldade:

1. **README no repositório e no PyPI**  
   - Instruções de instalação (`pip install data-economist`).  
   - Exemplos mínimos de uso (como acima).  
   - Opcional: link para documentação em `docs/` ou para um site.

2. **Documentação das funções**  
   - Docstrings nas funções (o que fazem, parâmetros, valor de retorno).  
   - Exemplos nos docstrings ou em `docs/` (como em [estrutura-projeto.md](estrutura-projeto.md)).

3. **Dependências declaradas**  
   - Todas as dependências em `pyproject.toml` (ex.: `pandas`, `requests`).  
   Assim, `pip install data-economist` instala tudo o que é necessário.

4. **Licença clara**  
   - Ficheiro LICENSE e menção no README.  
   Assim, a comunidade sabe se pode usar em projetos pessoais, académicos ou comerciais.

Quando isso estiver feito, os utilizadores conseguem instalar o pacote e usar as suas funções de dados económicos de forma fácil, tal como descrito neste guia.
