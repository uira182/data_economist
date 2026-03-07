# data_economist

Pacote Python para **analistas** e **consultoria económica** com duas vertentes:

1. **Fontes de dados** — obter dados de fontes públicas: **IBGE**, **Banco Central** (BCB SGS), **ComexStat** (MDIC) e **EIA** (Energy Information Administration).
2. **Funcionalidades** — ferramentas de análise, como **dessazonalização** de séries temporais com **X-13ARIMA-SEATS**.

Pensado para ser usado como biblioteca instalável por qualquer pessoa da área.

---

## Autor

**Uirá de Souza**  
Desenvolvedor há mais de 10 anos, formado em Ciência da Computação.  
E-mail: [uira182@hotmail.com](mailto:uira182@hotmail.com)  
Telefone: +55 18 98151-7906  

Estamos **abertos a melhorias**. Se tiver ideias ou sugestões, pode entrar em contacto pelo e-mail acima ou abrindo uma Issue / Pull Request no [repositório no GitHub](https://github.com/uiradesouza/data_economist).

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

### Fontes de dados

#### IBGE (SIDRA e metadados)

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

Documentação: [docs/fonte-ibge.md](docs/fonte-ibge.md).

#### BCB SGS (Banco Central — séries temporais)

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

Documentação: [docs/fonte-bcb-sgs.md](docs/fonte-bcb-sgs.md).

#### ComexStat (MDIC — comércio exterior)

```python
from data_economist import comexstat

# POST /historical-data — body no padrão da documentação oficial
body = {
    "flow": "export",
    "monthDetail": False,
    "period": {"from": "2018-01", "to": "2018-01"},
    "filters": [{"filter": "state", "values": [26]}],
    "details": ["country", "state"],
    "metrics": ["metricFOB", "metricKG"],
}
resultado = comexstat.get(body)

# GET /general — por CUCI Grupo ou posição SH4 (dados em resultado["data"]["list"])
dados = comexstat.get_general("export", "cuciGroup", ["281b"], "metricFOB")

# Filtro guardado no site — por ID ou URL da página geral
dados = comexstat.get_by_filter(146862)
dados = comexstat.get_by_filter("https://comexstat.mdic.gov.br/pt/geral/146862")
registos = dados["data"]["list"]
```

Documentação: [docs/fonte-comexstat.md](docs/fonte-comexstat.md). API oficial: [ComexStat MDIC](https://api-comexstat.mdic.gov.br/docs).

#### EIA (U.S. Energy Information Administration)

Requer **token de API** no ficheiro `.env`: `TOKEN_EIA=seu_token` (obtenha em [eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php)).

```python
from data_economist import eia

# Por URL completa
dados = eia.get_data("https://api.eia.gov/v2/steo/data/?frequency=monthly&...")

# Por parâmetros (STEO e Petroleum — mapeamento landing Databricks)
dados = eia.get_steo("PATC_WORLD", "monthly")
dados = eia.get_petroleum("pri/spt", "EER_EPMRU_PF4_RGC_DPG", "daily")

# Todos os dados de um setor e frequência
tudo = eia.get_by_landing("petroleo", "monthly")  # dict série → lista de registos
```

Documentação: [docs/fonte-eia.md](docs/fonte-eia.md).

### Funcionalidades

#### Dessazonalização (X-13ARIMA-SEATS)

O módulo **x13** não é uma fonte de dados: é uma **funcionalidade** para ajuste sazonal de séries que já tenhas (por exemplo obtidas do BCB ou do IBGE). Requer **x13binary** (`pip install x13binary`) e, na primeira utilização, `x13.init(project_root=raiz)`.

```python
from data_economist import bcb_sgs, x13
import pandas as pd

dados = bcb_sgs.get(433)  # IPCA
df = pd.DataFrame(dados)
df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
serie = df.set_index("data")["valor"].astype(float)
serie = serie.resample("ME").last().dropna()

x13.init(project_root=".")  # uma vez por projeto
modelo = x13.seas(serie, title="IPCA")
valor_dessaz = x13.final(modelo)  # série dessazonalizada
```

Documentação: [docs/fonte-x13.md](docs/fonte-x13.md) (requisitos, API, diagnósticos).

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
- **Fontes de dados:** [IBGE](docs/fonte-ibge.md) · [BCB SGS](docs/fonte-bcb-sgs.md) · [ComexStat](docs/fonte-comexstat.md) · [EIA](docs/fonte-eia.md)
- **Funcionalidades:** [Dessazonalização X-13](docs/fonte-x13.md)
- [Plano ComexStat (MDIC)](docs/planos/plano-comexstat.md)
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
