# data_economist

Pacote Python para **analistas** e **consultoria económica** com duas vertentes:

1. **Fontes de dados** — obter dados de fontes públicas: **IBGE**, **Banco Central** (BCB SGS), **ComexStat** (MDIC), **EIA** (Energy Information Administration) e **FRED** (Federal Reserve Bank of St. Louis).
2. **Funcionalidades** — ferramentas de análise: **dessazonalização** X-13ARIMA-SEATS, **tratamento de séries** (filtros, suavização, frequência, whitening), **estatística** (descritiva, normalidade, correlação, testes de hipótese, contingência, PCA e fatorial), **modelos de séries temporais** (AR, MA, ARMA, ARIMA, SARIMA, ARMAX, ARFIMA, testes de raiz unitária, auto seleção e previsão) e **regressão** (OLS/WLS/NLS, robusta, quantílica, stepwise, PDL, ARDL, TAR/SETAR/STAR).

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

O `pip` instala automaticamente as dependências listadas abaixo. Se instalar manualmente, use Python 3.9 ou superior.

### Dependências (instaladas automaticamente com o pacote)

| Pacote | Versão mínima | Uso principal |
|--------|----------------|---------------|
| pandas | 1.3.0 | Fontes de dados, tratamento, estatística, modelos, regressão |
| requests | 2.26.0 | BCB SGS, EIA, FRED, ComexStat (requisições HTTP) |
| statsmodels | 0.13.0 | Tratamento (filtros, suavização), modelos (ARIMA, raiz unitária), regressão |
| scipy | 1.7.0 | Estatística (testes, distribuições), regressão NLS |

Opcionais para desenvolvimento e testes: `pytest`, `black`, `ruff`, `python-dotenv` (instaláveis com `pip install -e ".[dev]"`).

### Créditos e bibliotecas externas

Parte dos cálculos usa bibliotecas externas; os créditos dos algoritmos são dos respectivos projetos. O **statsmodels** é usado para modelos ARIMA, filtros, suavização, regressão e parte da estatística — pode usar essas funções pela nossa API (nomes e resultados padronizados) ou diretamente pelo statsmodels. O **X-13ARIMA-SEATS** (Census Bureau) e o **x13binary** fornecem o binário de dessazonalização; nós integramos em Python (especificação, execução e leitura dos resultados). Detalhes: [Créditos e bibliotecas externas](docs/creditos-bibliotecas.md).

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

#### FRED (Federal Reserve Economic Data)

Requer **token de API** no arquivo `.env`: `TOKEN_FRED=seu_token` (registro gratuito em [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)).

```python
from data_economist import fred

# Observações de uma série (série completa ou com filtro de datas)
dados = fred.get("CPIAUCSL")
dados = fred.get("FEDFUNDS", date_init="2010-01-01", date_end="2024-12-31")
dados = fred.get("CPIAUCSL", units="pc1")          # variação % a/a
dados = fred.get("VIXCLS")                         # VIX diário
dados = fred.get("SP500")                          # S&P 500

# Metadados da série
meta = fred.metadados("CPIAUCSL")
# meta["title"], meta["frequency"], meta["units"], meta["observation_start"]

# Busca por texto
series = fred.buscar("consumer price index", limit=20)

# Séries do notebook de ingestão (mapeamento landing Databricks)
fred.SERIES_FRED["daily"]["pol_mon"]       # DTWEXBGS, VIXCLS, SP500...
fred.SERIES_FRED["monthly"]["pol_mon"]     # CPIAUCSL, FEDFUNDS, UNRATE...
fred.SERIES_FRED["monthly"]["min_sid"]     # PPI minério/siderurgia
```

Documentação: [docs/fonte-fred.md](docs/fonte-fred.md).

### Funcionalidades

#### Tratamento de séries temporais

O módulo **tratamento** aplica transformações e análises sobre séries que já existem.

```python
from data_economist import tratamento

# Filtros de ciclo e tendência
r = tratamento.hp(serie)          # Hodrick-Prescott
r = tratamento.bk(serie)          # Baxter-King
r = tratamento.cf(serie)          # Christiano-Fitzgerald
print(r.ciclo, r.tendencia)

# Suavização exponencial
r = tratamento.holt_winters(serie_mensal)   # Holt-Winters (m inferido automaticamente)
r = tratamento.ets(serie)                   # ETS automático (seleciona por AIC)
print(r.suavizado)

# Conversão de frequência
mensal  = tratamento.para_frequencia(serie_diaria, "ME", metodo="mean")
diario  = tratamento.para_frequencia(serie_mensal, "D",  metodo="cubic")

# Whitening AR(p)
r = tratamento.whitening(serie)
print(r.lags, r.residuos)
```

Documentação: [docs/fonte-tratamento.md](docs/fonte-tratamento.md).

#### Estatística

O módulo **estatistica** oferece análises estatísticas completas sobre séries e DataFrames.

```python
import data_economist.estatistica as est

# Descritiva
r = est.resumo(serie)
print(r.media, r.desvio_padrao, r.jb_pvalue)

# Normalidade
print(est.lilliefors(serie))
print(est.anderson_darling(serie))

# Correlação
r = est.pearson(x, y)
print(f"r={r.coeficiente:.3f}  p={r.pvalue:.4f}  IC={r.intervalo_confianca}")
cov = est.covariancia(df)
corr = est.matriz_correlacao(df, metodo="spearman")

# Testes de hipótese
print(est.ttest(grupo_a, grupo_b))
print(est.anova(g1, g2, g3))
print(est.mann_whitney(x, y))
print(est.levene(g1, g2, g3))

# Tabelas de contingência
r = est.cruzar(df["produto"], df["regiao"])
print(r.v_cramer, r.chi2_pvalue)

# Análise multivariada
r = est.pca(df, n_componentes=3)
print(r.variancia_explicada)
r = est.fatorial(df, n_fatores=2, rotacao="varimax")
print(r.cargas)
```

Documentação: [docs/fonte-estatistica.md](docs/fonte-estatistica.md).

#### Modelos de séries temporais

O módulo **modelos** cobre modelagem univariada completa (AR, MA, ARMA, ARIMA, SARIMA, ARMAX, ARFIMA, raiz unitária, seleção e previsão).

```python
from data_economist import modelos

# Ajuste de modelos
r1 = modelos.arima(serie, p=1, d=1, q=1)
r2 = modelos.sarima(serie, p=1, d=1, q=1, P=1, D=0, Q=1, s=12)

# Seleção automática
melhor = modelos.auto_arima(serie, max_p=4, max_q=4, max_d=2, criterio="aic")

# Testes de raiz unitária
print(modelos.adf(serie))
print(modelos.kpss(serie))

# Previsão
prev = modelos.prever(melhor, steps=12)
print(prev.valores.tail())
```

Documentação: [docs/fonte-modelos.md](docs/fonte-modelos.md).

#### Regressão (equação única)

O módulo **regressao** cobre estimação de equação única e seleção de variáveis (OLS, WLS, NLS, robusta, quantílica, stepwise, PDL, ARDL, TAR/SETAR/STAR).

```python
from data_economist import regressao as reg

r = reg.ols(y, X, cov_type="HC1")
rq = reg.quantilica(y, X, q=0.5)
sw = reg.stepwise(y, X, metodo="both", criterio="aic")
rpdl = reg.pdl(y, x, lags=4, grau=2)
rtar = reg.tar(y, lag=1)
```

Documentação: [docs/fonte-regressao.md](docs/fonte-regressao.md).

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
- **Funcionalidades:** [Dessazonalização X-13](docs/fonte-x13.md) · [Tratamento de séries](docs/fonte-tratamento.md) · [Estatística](docs/fonte-estatistica.md) · [Modelos de séries temporais](docs/fonte-modelos.md) · [Regressão](docs/fonte-regressao.md)
- [Plano ComexStat (MDIC)](docs/planos/plano-comexstat.md)
- [Guia de publicação no PyPI](docs/guia-publicacao-pacote.md)
- [Estrutura do projeto](docs/estrutura-projeto.md)
- [Uso pelo utilizador](docs/uso-pelo-utilizador.md)
- [Créditos e bibliotecas externas](docs/creditos-bibliotecas.md)

---

## Licença

MIT. Ver [LICENSE](LICENSE).

---

## Contribuir

O projeto é **livre** e público no GitHub: issues e pull requests são bem-vindos. O código está sob licença MIT e pode ser usado e adaptado conforme a licença.

**Governança:** o mantenedor (dono do repositório) **aprova os merges para a branch `main`** (via [CODEOWNERS](.github/CODEOWNERS)) e **gera as atualizações do pacote** (releases e publicação no PyPI). Assim, contribuições entram após revisão, e as novas versões são publicadas de forma centralizada.

Ver documentação em `docs/` para como publicar releases e como utilizadores podem instalar e usar o pacote.
