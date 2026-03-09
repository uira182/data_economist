# Créditos e bibliotecas externas

O **data_economist** utiliza bibliotecas externas para parte dos cálculos. Sempre que isso ocorre, os **créditos dos algoritmos e do software** pertencem aos respectivos projetos; o **diferencial do data_economist** é a integração, a API unificada, o formato de saída e a documentação voltada ao uso em análise económica.

Regra adotada no projeto: **se não for implementação própria, damos crédito ao projeto externo e deixamos explícito até onde o usamos e qual é a vantagem de usar a nossa ferramenta.**

---

## statsmodels

**Crédito:** Os cálculos de modelos AR/MA/ARMA/ARIMA/SARIMA/ARMAX, filtros de ciclo e tendência, suavização exponencial, testes de raiz unitária, regressão (OLS, WLS, robusta, quantílica), ARDL, análise fatorial e parte dos testes estatísticos são realizados pelo pacote [statsmodels](https://www.statsmodels.org/).

**Onde usamos no data_economist:**

| Módulo | Uso do statsmodels |
|--------|---------------------|
| **modelos** | AR (`AutoReg`), MA/ARMA/ARIMA (`ARIMA`), SARIMA/ARMAX (`SARIMAX`), ADF/PP/KPSS/Zivot-Andrews, ACF/PACF, Ljung-Box. O ARFIMA usa estimador GPH e diferença fracionária implementados no próprio data_economist; o ajuste ARMA final usa `ARIMA` do statsmodels. |
| **tratamento** | Filtros Hodrick-Prescott, Baxter-King e Christiano-Fitzgerald; suavização (SES, Holt, Holt-Winters, ETS); whitening AR(p). |
| **estatistica** | Teste de Lilliefors (normalidade); análise fatorial e rotações. |
| **regressao** | OLS, WLS, regressão robusta (Huber/Bisquare), regressão quantílica, VIF; ARDL. |

**Como usar:** Você pode usar os mesmos cálculos de duas formas:

1. **Pela nossa aplicação** — funções com nomes e assinaturas padronizadas e resultados em dataclasses (ex.: `modelos.arima()`, `modelos.prever()`, `regressao.ols()`). Indicado quando quer uma API única, saída consistente e documentação integrada.
2. **Diretamente pelo statsmodels** — importe e use o statsmodels como em qualquer projeto Python (ex.: `from statsmodels.tsa.arima.model import ARIMA`). Indicado quando precisa de opções avançadas ou do objeto nativo do statsmodels.

**Referência:** [statsmodels — Statistical models in Python](https://www.statsmodels.org/).

---

## X-13ARIMA-SEATS e x13binary

**Crédito:** O programa **X-13ARIMA-SEATS** é do **US Census Bureau** e constitui o método oficial de ajuste sazonal usado por várias agências estatísticas. No Python, o executável é fornecido pelo pacote [x13binary](https://pypi.org/project/x13binary/) (PyPI).

**Onde usamos no data_economist:** O módulo **x13** do data_economist não implementa o algoritmo de dessazonalização: ele **utiliza** o binário X-13 (via x13binary). O que é **nosso** é a integração em Python: construção do ficheiro de especificação (.spc), invocação do executável, leitura e interpretação dos ficheiros de saída (.udg, .html, .s11–.s13) e exposição dos resultados em objetos padronizados (`SeasonalResult`, séries dessazonalizada, tendência, irregular, etc.). Ou seja, **os créditos dos cálculos são do Census Bureau e do x13binary; o crédito da manipulação, da interface e do resultado exposto ao utilizador é do data_economist.**

**Referências:**
- [X-13ARIMA-SEATS (US Census Bureau)](https://www.census.gov/data/software/x13as.html)
- [x13binary (PyPI)](https://pypi.org/project/x13binary/)

---

## Outras dependências

- **pandas** — manipulação de séries e dados; não reimplementamos estruturas de dados.
- **requests** — requisições HTTP às APIs (BCB, EIA, FRED, ComexStat).
- **scipy** — testes estatísticos, distribuições e otimização (ex.: NLS); crédito dos métodos numéricos ao SciPy.

Para a lista completa de dependências e versões, consulte o [pyproject.toml](../pyproject.toml) e a secção [Dependências](README.md#dependências-instaladas-automaticamente-com-o-pacote) no README.
