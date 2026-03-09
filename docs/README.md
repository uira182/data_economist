# Documentação — data_economist

Bem-vindo à documentação do **data_economist**. O pacote oferece:

- **Fontes de dados** — obter dados de fontes públicas (IBGE, Banco Central, ComexStat, EIA, FRED).
- **Funcionalidades** — ferramentas de análise: dessazonalização X-13, tratamento de séries temporais, análise estatística, modelos de séries temporais e regressão.

## Conteúdo da documentação

### Fontes de dados

| Documento | Descrição |
|-----------|-----------|
| [Fonte IBGE](fonte-ibge.md) | Módulo **ibge**: `get(t,n,v,p,c)`, `url()`, `metadados(tabela)` |
| [Fonte BCB SGS](fonte-bcb-sgs.md) | Módulo **bcb_sgs**: `get(codigo, date_init, date_end)` — séries do Banco Central (SGS) |
| [Fonte ComexStat](fonte-comexstat.md) | Módulo **comexstat**: `get(body)`, `get_general(...)`, `get_by_filter(id\|url)` — comércio exterior (MDIC) |
| [Fonte EIA](fonte-eia.md) | Módulo **eia**: `get_data`, `get_steo`, `get_petroleum`, `get_by_landing` — dados energéticos; requer **TOKEN_EIA** no .env |
|| [Fonte FRED](fonte-fred.md) | Módulo **fred**: `get`, `metadados`, `buscar`, `categorias`, `tags`, `release` — Federal Reserve Bank (800k+ séries); requer **TOKEN_FRED** no .env |

### Funcionalidades

| Documento | Descrição |
|-----------|-----------|
| [Dessazonalização X-13](fonte-x13.md) | Módulo **x13**: `init`, `seas`, `final`, `trend`, `udg`, `summary` — ajuste sazonal X-13ARIMA-SEATS; requer **x13binary** |
| [Tratamento de séries](fonte-tratamento.md) | Módulo **tratamento**: filtros HP/BK/CF, suavização SES/DES/Holt/Holt-Winters/ETS, conversão de frequência e whitening AR(p) |
| [Estatística](fonte-estatistica.md) | Módulo **estatistica**: descritiva, normalidade, correlação, testes de hipótese, contingência, PCA e análise fatorial |
| [Modelos de séries temporais](fonte-modelos.md) | Módulo **modelos**: AR/MA/ARMA/ARIMA/SARIMA/ARMAX, ARFIMA (GPH), auto seleção, ACF/PACF, testes de raiz unitária e previsão |
| [Regressão](fonte-regressao.md) | Módulo **regressao**: OLS/WLS/NLS, robusta, quantílica, stepwise, PDL, ARDL e TAR/SETAR/STAR |

### Créditos

| Documento | Descrição |
|-----------|-----------|
| [Créditos e bibliotecas externas](creditos-bibliotecas.md) | statsmodels, X-13/x13binary: onde usamos, créditos e diferencial do data_economist; uso pela nossa API ou direto pela biblioteca. |

### Outros

| Documento | Descrição |
|-----------|-----------|
| [Antes do commit](antes-do-commit.md) | O que não deve ir para o GitHub e verificação antes do push / PyPI |
| [Guia de publicação do pacote](guia-publicacao-pacote.md) | Como criar, empacotar e publicar o pacote para a comunidade (PyPI, etc.) |
| [Estrutura do projeto](estrutura-projeto.md) | Estrutura de pastas e ficheiros recomendada para o pacote |
| [Uso pelo utilizador](uso-pelo-utilizador.md) | Como os utilizadores instalam e usam as funções do pacote |
| [Testar instalação local](testar-instalacao-local.md) | Testar o pacote no seu PC antes de publicar no PyPI |
| [Como testar (pytest)](como-testar.md) | Extensões no Cursor e como rodar os testes em Python |

## Projeto e autor

Pacote desenvolvido por **Uirá de Souza** (desenvolvedor há mais de 10 anos, formado em Ciência da Computação), pensado para analistas e consultoria económica. Publicado no GitHub e no PyPI para uso pela comunidade.

O projeto é **livre** (código aberto, licença MIT). O mantenedor **aprova os merges para a `main`** e **publica as atualizações do pacote** (releases no GitHub e no PyPI), de modo a manter um fluxo estável de versões.

**Configuração e token PyPI:** ver [config/README.md](../config/README.md) na pasta `config/` para onde guardar o token e como usá-lo na publicação.

Estamos **abertos a melhorias**. Se tiver ideias, sugestões ou quiser reportar um problema, entre em contacto através do [repositório no GitHub](https://github.com/uiradesouza/data_economist) (Issues ou Pull Requests) ou por e-mail (ver [README principal](../README.md)).

## Objetivo do projeto

- **Fontes de dados** — funções para obter dados de fontes públicas (IBGE, Banco Central, ComexStat, EIA, FRED).
- **Funcionalidades** — ferramentas de análise: dessazonalização (X-13), tratamento de séries temporais, análise estatística, modelos de séries temporais e regressão.
- **Publicação** como pacote Python instalável via `pip`.
- **Comunidade** — qualquer pessoa pode instalar e usar: `pip install data-economist`.

Comece pelo [Guia de publicação do pacote](guia-publicacao-pacote.md) para configurar tudo do zero.
