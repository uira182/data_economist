"""
Módulo IBGE — APIs do Instituto Brasileiro de Geografia e Estatística.

Inclui a API SIDRA (Sistema IBGE de Recuperação Automática).
Documentação: https://apisidra.ibge.gov.br

A SIDRA trabalha com dimensões D1 a D9: cada uma tem código (D1C, D2C, ...) e nome (D1N, D2N, ...).
Colunas fixas: NC, NN, MC, MN, V.

Constantes úteis: COLUNAS_DIMENSAO_CODIGO, COLUNAS_DIMENSAO_NOME, DIMENSOES_SIDRA.

Uso::

    from data_economist import ibge
    dados = ibge.url("https://apisidra.ibge.gov.br/values/t/8888/...")
    # ou várias URLs: resultados aninhados num único JSON (lista de listas/dicts)
    varios = ibge.url([url1, url2])
"""
from __future__ import annotations

import csv
import io
import json
import requests

_BASE_SIDRA = "https://apisidra.ibge.gov.br"
_BASE_AGREGADOS = "https://servicodados.ibge.gov.br/api/v3/agregados"

# Dimensões SIDRA: a API usa D1C/D1N até D9C/D9N (C=código, N=nome). Cada tabela pode usar 1 a 9.
# Colunas fixas da API: NC, NN, MC, MN, V.
COLUNAS_DIMENSAO_CODIGO = [f"D{i}C" for i in range(1, 10)]  # D1C, D2C, ..., D9C
COLUNAS_DIMENSAO_NOME = [f"D{i}N" for i in range(1, 10)]    # D1N, D2N, ..., D9N
DIMENSOES_SIDRA = tuple(
    f"D{i}{s}" for i in range(1, 10) for s in ("C", "N")    # D1C, D1N, D2C, D2N, ..., D9C, D9N
)


def url(url_or_urls: str | list[str]) -> list | dict:
    """
    Consulta uma ou várias URLs da API IBGE (ex.: SIDRA) e devolve os dados em JSON.

    Aceita uma **única URL** (str) ou uma **lista de URLs** ([url, url, ...]).
    Com lista, os resultados vêm aninhados num único JSON: uma lista onde cada
    elemento é o resultado da URL na mesma posição.

    A URL pode ser passada com ``formato=json`` ou sem; se for SIDRA, o pedido
    é feito pedindo JSON. Se a resposta vier em outro formato (ex.: CSV), é
    convertida para estrutura JSON.

    Parâmetros
    ----------
    url_or_urls : str | list[str]
        Uma URL completa da consulta (ex.: API SIDRA) ou uma lista de URLs.
        Ex.: ``"https://apisidra.ibge.gov.br/values/t/8888/..."`` ou
        ``[url1, url2]``.

    Retornos
    --------
    list | dict
        - **Uma URL:** o resultado dessa consulta (lista de dicts ou dict).
        - **Várias URLs:** lista de resultados na mesma ordem das URLs,
          ex.: ``[resultado_url1, resultado_url2, ...]``. Um único JSON aninhado.
        Sempre serializável com ``json.dumps()``.
        Na API SIDRA, o primeiro elemento de cada lista costuma ser o cabeçalho;
        as dimensões usam colunas D1C, D1N, ..., D9C, D9N.

    Raises
    ------
    requests.HTTPError
        Se alguma resposta HTTP indicar erro (ex.: 404, 500).

    Exemplos
    --------
    >>> from data_economist import ibge
    >>> u = "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/last/c544/129317"
    >>> dados = ibge.url(u)
    >>> isinstance(dados, list)
    True
    >>> # Várias URLs: resultado aninhado
    >>> varios = ibge.url([u, u])
    >>> len(varios) == 2 and isinstance(varios[0], list)
    True
    """
    if isinstance(url_or_urls, str):
        return _url_uma(url_or_urls)
    return [_url_uma(u) for u in url_or_urls]


def _url_uma(url: str) -> list | dict:
    """Consulta uma única URL e devolve o resultado em JSON."""
    url = _garantir_formato_json_sidra(url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return _ler_resposta_como_json(response)


def get(
    t: int | str,
    n: tuple[int | str, str] | None = None,
    v: int | str | None = None,
    p: str | None = None,
    c: tuple[int | str, int | str] | list[tuple[int | str, int | str]] | None = None,
    d: str | None = None,
) -> list | dict:
    """
    Consulta a API SIDRA montando a URL a partir dos parâmetros. Retorna sempre JSON.

    Parâmetros
    ----------
    t : int | str
        Tabela (ex.: 8888).
    n : tuple (nível, valor) ou None
        Região: (nível, valor), ex. (3, "all") para n3/all (UF, todos).
    v : int | str ou None
        Variável (ex.: 12606).
    p : str ou None
        Período: "all", "first", "last" ou código específico.
    c : tuple (id_class, id_cat) ou lista de tuples, ou None
        Classificação: (544, 129317) ou [(544, 129317), ...].
    d : str ou None
        Formato decimal (ex.: "v12606%205" para variável 12606, 5 decimais).

    Retornos
    --------
    list | dict
        Resposta da API em JSON. Em erro HTTP, levanta requests.HTTPError.

    Exemplos
    --------
    >>> ibge.get(8888)
    >>> ibge.get(8888, n=(3, "all"))
    >>> ibge.get(8888, n=(3, "all"), v=12606, p="first", c=(544, 129317))
    """
    path = ["values", "t", str(t)]
    if n is not None:
        path.extend([f"n{n[0]}", str(n[1])])
    if v is not None:
        path.extend(["v", str(v)])
    if p is not None:
        path.extend(["p", str(p)])
    if c is not None:
        if isinstance(c, (list, tuple)) and len(c) == 2 and not isinstance(c[0], tuple):
            path.extend([f"c{c[0]}", str(c[1])])
        else:
            for par in c:
                path.extend([f"c{par[0]}", str(par[1])])
    if d is not None:
        path.extend(["d", str(d)])
    url_completa = f"{_BASE_SIDRA}/{'/'.join(path)}"
    url_completa = _garantir_formato_json_sidra(url_completa)
    response = requests.get(url_completa, timeout=30)
    response.raise_for_status()
    return _ler_resposta_como_json(response)


def metadados(tabela: int | str) -> dict:
    """
    Obtém os metadados de uma tabela do IBGE (agregados/SIDRA) pelo número da tabela.

    Utiliza a API: ``https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados``.
    O resultado inclui id, nome, URL, pesquisa, assunto, periodicidade, nivelTerritorial,
    variaveis e classificacoes.

    Parâmetros
    ----------
    tabela : int | str
        Número da tabela (ex.: 8888 para Produção Física Industrial).

    Retornos
    --------
    dict
        Metadados em JSON (id, nome, URL, pesquisa, assunto, periodicidade,
        nivelTerritorial, variaveis, classificacoes).

    Raises
    ------
    requests.HTTPError
        Se a resposta HTTP indicar erro (ex.: tabela inexistente).

    Exemplos
    --------
    >>> from data_economist import ibge
    >>> meta = ibge.metadados(8888)
    >>> meta["nome"]
    'Produção Física Industrial, por seções e atividades industriais'
    >>> "variaveis" in meta
    True
    """
    tabela = str(int(tabela))
    url = f"{_BASE_AGREGADOS}/{tabela}/metadados"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def _garantir_formato_json_sidra(url: str) -> str:
    """Para URLs da SIDRA, garante que o pedido peça formato JSON."""
    if _BASE_SIDRA not in url:
        return url
    if "formato=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}formato=json"


def _ler_resposta_como_json(response: requests.Response) -> list | dict:
    """
    Lê o corpo da resposta, identifica o formato (JSON, CSV, etc.)
    e devolve sempre uma estrutura JSON (list ou dict).
    """
    content_type = (response.headers.get("Content-Type") or "").lower()
    text = response.text

    # 1) Tentar JSON (Content-Type ou conteúdo)
    if "application/json" in content_type:
        return response.json()
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError):
        pass

    # 2) CSV ou texto tabular
    if "text/csv" in content_type or "text/plain" in content_type:
        return _csv_para_lista_dicts(text)
    if _parece_csv(text):
        return _csv_para_lista_dicts(text)

    # 3) Fallback: devolver conteúdo bruto numa estrutura JSON
    return [{"raw": text}]


def _parece_csv(text: str) -> bool:
    """Heurística: tem vírgulas ou pontos-e-vírgulas e várias linhas."""
    if not text or not text.strip():
        return False
    linhas = text.strip().splitlines()
    if len(linhas) < 2:
        return False
    primeira = linhas[0]
    return "," in primeira or ";" in primeira


def _csv_para_lista_dicts(text: str) -> list[dict]:
    """Converte texto CSV em lista de dicionários (primeira linha = chaves)."""
    # Detectar delimitador
    primeira_linha = text.strip().splitlines()[0] if text.strip() else ""
    delimiter = ";" if ";" in primeira_linha and "," not in primeira_linha else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return list(reader)
