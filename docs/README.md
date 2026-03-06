# Documentação — data_economist

Bem-vindo à documentação do **data_economist**, um pacote Python para baixar dados de fontes económicas de forma fácil, pensado para ser publicado e usado pela comunidade.

## Conteúdo da documentação

| Documento | Descrição |
|----------|-----------|
| [Fonte IBGE](fonte-ibge.md) | Documentação do módulo **ibge**: `get(t,n,v,p,c)`, `url()`, `metadados(tabela)` |
| [Fonte BCB SGS](fonte-bcb-sgs.md) | Documentação do módulo **bcb_sgs**: `get(codigo, date_init, date_end)` — séries do Banco Central (SGS) |
| [Fonte ComexStat](fonte-comexstat.md) | Documentação do módulo **comexstat**: `get(body)`, `get_general(...)`, `get_filter(id)`, `get_by_filter(id\|url)` — comércio exterior (MDIC) |
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

## Objetivo do projeto

- **Funções** para descarregar dados de fontes económicas (BCE, Eurostat, IMF, etc.).
- **Publicação** como pacote Python instalável via `pip`.
- **Comunidade** — qualquer pessoa pode instalar e usar: `pip install data-economist`.

Comece pelo [Guia de publicação do pacote](guia-publicacao-pacote.md) para configurar tudo do zero.
