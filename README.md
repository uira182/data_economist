# data_economist

Pacote Python para **analistas** e **consultoria económica**: funções para baixar dados de fontes económicas de forma fácil. Pensado para ser usado como biblioteca instalável por qualquer pessoa da área.

---

## Autor

**Uirá de Souza**  
Desenvolvedor há mais de 10 anos, formado em Ciência da Computação.  
E-mail: [uira182@hotmail.com](mailto:uira182@hotmail.com)  
Telefone: +55 18 98151-7906  

---

## Instalação

Quando o pacote estiver publicado no PyPI:

```bash
pip install data-economist
```

Em desenvolvimento (a partir da pasta do projeto):

```bash
pip install -e .
```

---

## Uso

### Fonte IBGE (SIDRA e metadados)

```python
from data_economist import ibge

# Dados: uma URL ou lista de URLs (resultados aninhados num único JSON)
url = "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/last/c544/129317"
dados = ibge.url(url)           # lista de dicts (1º = cabeçalho, resto = registos)
# varios = ibge.url([url1, url2])  # [resultado1, resultado2]

# Metadados: número da tabela (ex.: 8888 = Produção Física Industrial)
meta = ibge.metadados(8888)
# meta["nome"], meta["variaveis"], meta["classificacoes"], meta["periodicidade"], etc.
```

Documentação completa da fonte IBGE: [docs/fonte-ibge.md](docs/fonte-ibge.md).

### Fonte BCB SGS (Banco Central — séries temporais)

```python
from data_economist import bcb_sgs

# Série completa (último valor → para trás, de 10 em 10 anos)
dados = bcb_sgs.get(433)   # 433 = IPCA

# Com datas: início, ou fim, ou intervalo (formato YYYY-MM-DD)
dados = bcb_sgs.get(433, "2020-01-01")              # de 2020 até o último valor
dados = bcb_sgs.get(433, None, "2000-01-06")       # de 2000-01-06 para trás
dados = bcb_sgs.get(433, "2020-01-01", "2025-01-01")  # só o intervalo 2020–2025
# Cada item: {"data": "DD/MM/YYYY", "valor": "..."}
```

Documentação completa da fonte BCB SGS: [docs/fonte-bcb-sgs.md](docs/fonte-bcb-sgs.md).  
Outras fontes (BCE, Eurostat, IMF) serão documentadas em [docs/](docs/).

---

## Estrutura do projeto

```
data_economist/
├── src/data_economist/   # Código do pacote
├── docs/                 # Documentação
├── tests/                # Testes
├── config/               # Exemplo de configuração (token PyPI)
├── pyproject.toml
└── README.md
```

---

## Documentação

- [Índice da documentação](docs/README.md)
- [Fonte IBGE (get e metadados)](docs/fonte-ibge.md)
- [Fonte BCB SGS (Banco Central — séries temporais)](docs/fonte-bcb-sgs.md)
- [Guia de publicação no PyPI](docs/guia-publicacao-pacote.md)
- [Estrutura do projeto](docs/estrutura-projeto.md)
- [Uso pelo utilizador](docs/uso-pelo-utilizador.md)

---

## Licença

MIT. Ver [LICENSE](LICENSE).

---

## Contribuir

O projeto é **livre** e público no GitHub: issues e pull requests são bem-vindos. O código está sob licença MIT e pode ser usado e adaptado conforme a licença.

**Governança:** o mantenedor (dono do repositório) **aprova os merges para a branch `main`** (via [CODEOWNERS](.github/CODEOWNERS)) e **gera as atualizações do pacote** (releases e publicação no PyPI). Assim, contribuições entram após revisão, e as novas versões são publicadas de forma centralizada.

Ver documentação em `docs/` para como publicar releases e como utilizadores podem instalar e usar o pacote.
