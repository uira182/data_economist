"""
Módulo FRED — Federal Reserve Economic Data (St. Louis Fed).

Requer token de API em variável de ambiente TOKEN_FRED (ou FRED_API_KEY).
Registro gratuito: https://fred.stlouisfed.org/docs/api/api_key.html

Uso::

    # No .env: TOKEN_FRED=seu_token
    from data_economist import fred

    # Observações de uma série
    dados = fred.get("CPIAUCSL")
    dados = fred.get("CPIAUCSL", date_init="2020-01-01", date_end="2024-12-31")

    # Metadados
    meta = fred.metadados("CPIAUCSL")

    # Busca por texto
    series = fred.buscar("consumer price index", limit=20)

    # Séries do notebook de ingestão
    fred.SERIES_FRED["monthly"]["pol_mon"]
"""
from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_BASE = "https://api.stlouisfed.org/fred"
_RETRY_TOTAL = 3
_RETRY_BACKOFF = 0.5
_FRED_REGISTER_URL = "https://fred.stlouisfed.org/docs/api/api_key.html"
_FRED_DOC_URL = "https://fred.stlouisfed.org/docs/api/fred/"
_MSG_TOKEN = (
    "Documentação FRED: "
    f"{_FRED_DOC_URL} | Registro de token: {_FRED_REGISTER_URL}"
)

# ---------------------------------------------------------------------------
# Séries de referência do notebook de ingestão (Databricks)
# ---------------------------------------------------------------------------
SERIES_FRED: dict[str, dict[str, list[str]]] = {
    "daily": {
        "pol_mon": [
            "DTWEXBGS",    # US Dollar Index — Broad
            "DTWEXAFEGS",  # US Dollar Index — economias avançadas
            "DTWEXEMEGS",  # US Dollar Index — emergentes
            "VIXCLS",      # VIX
            "SP500",       # S&P 500
        ],
        "quimicos": [
            "DEXCHUS",     # USD/CNY
        ],
    },
    "weekly": {},
    "monthly": {
        "min_sid": [
            "WPU101707",       # PPI Lingotes de aço
            "PPIACO",          # PPI todas as commodities
            "WPU107601",       # PPI Fio-máquina de aço
            "WPU1017",         # PPI Produtos ferrosos primários
            "WPU03T15M05",     # PPI Minas e pedreiras
            "PCU332618332618", # PPI Arames e eletrodos
            "PCU3312223312225",# PPI Aço laminado plano
            "WPU101704",       # PPI Placas e blocos de aço
        ],
        "petrol": [
            "WPU0543",  # PPI Petróleo bruto
            "WPU0531",  # PPI Gás natural
        ],
        "bk": [
            "PCU33312033312011",  # PPI Turbinas a gás industriais
            "PCU333131333131",    # PPI Bombas e compressores
            "PCU3331313331319",   # PPI Compressores de ar
            "PCU532412532412",    # PPI Aluguel de máquinas
            "PCU336510336510541", # PPI Aeronaves civis
            "A33HNO",             # Pedidos bens de capital não-aeronaves
            "WPU114908052",       # PPI Transformadores elétricos
            "IPB50001N",          # Produção industrial bens de capital
        ],
        "pol_mon": [
            "CPIAUCSL",   # CPI — todos os itens, SA
            "CPILFESL",   # CPI — core, SA
            "CUSR0000SAS",# CPI — serviços, SA
            "UNRATE",     # Taxa de desemprego
            "DFEDTARU",   # Fed Funds target — limite superior
            "DFEDTARL",   # Fed Funds target — limite inferior
            "FEDFUNDS",   # Fed Funds effective rate
            "RTWEXBGS",   # Real US Dollar Index — Broad
        ],
        "quimicos": [
            "PCU325220325220",    # PPI Resinas sintéticas
            "PCU325212325212P",   # PPI Plásticos em formas primárias
            "PCU325199325199P",   # PPI Outros químicos básicos
            "PCU326220326220P",   # PPI Embalagens plásticas
            "WPU031502412",       # PPI Etanol industrial
            "WPU06790918",        # PPI Especialidades químicas
            "PCU325325",          # PPI Produtos químicos em geral
        ],
    },
    "quarterly": {
        "pol_mon": [
            "CIU2013000000000I",  # Custo unitário do trabalho
        ],
    },
    "yearly": {},
}
"""Séries FRED organizadas por frequência e grupo temático (espelha notebook de ingestão)."""


# ---------------------------------------------------------------------------
# Exceção dedicada
# ---------------------------------------------------------------------------
class FredError(Exception):
    """Erro de comunicação ou resposta inválida da API FRED."""


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _get_token() -> str:
    """Obtém o token FRED de TOKEN_FRED (ou FRED_API_KEY) no ambiente."""
    _load_env()
    token = os.environ.get("TOKEN_FRED") or os.environ.get("FRED_API_KEY")
    if not token or not str(token).strip():
        raise ValueError(
            "Token FRED nao configurado. Crie um arquivo .env na raiz do projeto "
            "(pasta onde voce executa o codigo) e adicione uma linha: TOKEN_FRED=seu_token. "
            "Obtenha o token gratuito em: "
            f"{_FRED_REGISTER_URL} | Documentacao: {_FRED_DOC_URL}"
        )
    return str(token).strip()


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=_RETRY_TOTAL,
        connect=_RETRY_TOTAL,
        read=_RETRY_TOTAL,
        backoff_factor=_RETRY_BACKOFF,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _parse_date(value: str | datetime | None) -> str | None:
    """Converte date para string YYYY-MM-DD aceita pela API FRED."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    value = str(value).strip()
    datetime.strptime(value, "%Y-%m-%d")
    return value


def _request(
    session: requests.Session,
    url: str,
    timeout: int,
) -> dict:
    """Faz GET e retorna JSON. Lança FredError ou ValueError conforme o caso."""
    try:
        response = session.get(url, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        raise FredError(
            f"Falha de conexão com a API FRED. URL: {url}"
        ) from exc

    if response.status_code in (401, 403):
        raise ValueError(
            "Token FRED invalido ou nao autorizado. Verifique se no arquivo .env "
            "a linha TOKEN_FRED=seu_token esta correta. Token gratuito: "
            f"{_FRED_REGISTER_URL} | Docs: {_FRED_DOC_URL}"
        )
    if response.status_code == 404:
        raise FredError(f"Série ou recurso não encontrado na API FRED. URL: {url}")
    if response.status_code == 429:
        raise FredError(
            "Limite de requisições da API FRED atingido (HTTP 429). "
            "Aguarde alguns instantes e tente novamente."
        )
    if response.status_code >= 500:
        raise FredError(
            f"Erro interno da API FRED (HTTP {response.status_code}). Tente novamente mais tarde."
        )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise FredError(f"Erro HTTP na API FRED: {response.status_code}. URL: {url}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise FredError(f"A API FRED retornou JSON inválido. URL: {url}") from exc

    # Erros embutidos no JSON com status 200
    if isinstance(data, dict) and data.get("error_message"):
        msg = data["error_message"]
        if "api_key" in msg.lower():
            raise ValueError(
                f"Token FRED invalido (API respondeu: {msg}). "
                "Verifique no arquivo .env se a linha TOKEN_FRED=seu_token esta correta. "
                f"Token gratuito: {_FRED_REGISTER_URL} | Docs: {_FRED_DOC_URL}"
            )
        raise FredError(f"Erro da API FRED: {msg}. URL: {url}")

    return data


def _build_url(endpoint: str, params: dict) -> str:
    params["file_type"] = "json"
    return f"{_BASE}/{endpoint}?{urlencode(params)}"


def _convert_value(raw: str) -> float | None:
    """Converte o campo value da API: '.' vira None, demais viram float."""
    if raw is None or str(raw).strip() == ".":
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def get(
    series_id: str,
    date_init: str | datetime | None = None,
    date_end: str | datetime | None = None,
    units: str | None = None,
    frequency: str | None = None,
    aggregation_method: str | None = None,
    limit: int = 100_000,
    sort_order: str = "asc",
    timeout: int = 30,
    api_key: str | None = None,
) -> list[dict]:
    """
    Retorna as observações de uma série FRED.

    Parâmetros
    ----------
    series_id : str
        Código da série FRED (ex.: ``CPIAUCSL``, ``FEDFUNDS``, ``SP500``).
    date_init : str | datetime | None
        Data inicial ``YYYY-MM-DD``. Se None, usa o início da série.
    date_end : str | datetime | None
        Data final ``YYYY-MM-DD``. Se None, usa a data mais recente disponível.
    units : str | None
        Transformação: ``lin`` (nível), ``chg`` (variação absoluta), ``pch`` (variação %),
        ``pc1`` (variação % a/a), ``pca`` (taxa anualizada composta), ``log``.
    frequency : str | None
        Frequência de agregação: ``d``, ``w``, ``bw``, ``m``, ``q``, ``sa``, ``a``.
    aggregation_method : str | None
        Método de agregação: ``avg``, ``sum``, ``eop`` (end-of-period).
    limit : int
        Número máximo de observações (padrão 100.000).
    sort_order : str
        ``asc`` (padrão) ou ``desc``.
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    list[dict]
        Lista de registros ``{"date": "YYYY-MM-DD", "value": float | None}``.
        Valores ``"."`` (missing) são convertidos para ``None``.

    Exemplos
    --------
    >>> dados = fred.get("CPIAUCSL")
    >>> dados = fred.get("FEDFUNDS", date_init="2010-01-01", date_end="2024-12-31")
    >>> dados = fred.get("CPIAUCSL", units="pc1")          # variacao % a/a
    >>> dados = fred.get("CPIAUCSL", frequency="a", aggregation_method="avg")  # media anual
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()

    params: dict = {
        "series_id": series_id,
        "api_key": key,
        "limit": limit,
        "sort_order": sort_order,
    }

    d_init = _parse_date(date_init)
    d_end = _parse_date(date_end)
    if d_init:
        params["observation_start"] = d_init
    if d_end:
        params["observation_end"] = d_end
    if units:
        params["units"] = units
    if frequency:
        params["frequency"] = frequency
    if aggregation_method:
        params["aggregation_method"] = aggregation_method

    url = _build_url("series/observations", params)

    try:
        data = _request(session, url, timeout)
    except FredError as exc:
        # Algumas séries (ex.: SP500) não aceitam realtime_start/end — retenta sem eles
        if "400" in str(exc) or "Bad Request" in str(exc):
            params_alt = {k: v for k, v in params.items() if k not in ("realtime_start", "realtime_end")}
            url_alt = _build_url("series/observations", params_alt)
            data = _request(session, url_alt, timeout)
        else:
            raise
    finally:
        session.close()

    observations = data.get("observations", [])
    return [
        {"date": obs["date"], "value": _convert_value(obs.get("value"))}
        for obs in observations
    ]


def metadados(
    series_id: str,
    timeout: int = 30,
    api_key: str | None = None,
) -> dict:
    """
    Retorna os metadados de uma série FRED.

    Parâmetros
    ----------
    series_id : str
        Código da série FRED (ex.: ``CPIAUCSL``).
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    dict
        Dicionário com campos: ``id``, ``title``, ``frequency``, ``units``,
        ``seasonal_adjustment``, ``observation_start``, ``observation_end``,
        ``last_updated``, ``notes`` (pode estar ausente).

    Exemplos
    --------
    >>> meta = fred.metadados("CPIAUCSL")
    >>> meta["title"]
    'Consumer Price Index for All Urban Consumers: All Items in U.S. City Average'
    >>> meta["frequency"]
    'Monthly'
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()
    try:
        url = _build_url("series", {"series_id": series_id, "api_key": key})
        data = _request(session, url, timeout)
    finally:
        session.close()

    series_list = data.get("seriess", [])
    if not series_list:
        raise FredError(f"Série FRED '{series_id}' não encontrada.")
    return series_list[0]


def buscar(
    texto: str,
    limit: int = 100,
    order_by: str = "popularity",
    sort_order: str = "desc",
    filter_variable: str | None = None,
    filter_value: str | None = None,
    tag_names: str | None = None,
    timeout: int = 30,
    api_key: str | None = None,
) -> list[dict]:
    """
    Busca séries FRED por texto (full-text search).

    Parâmetros
    ----------
    texto : str
        Texto de busca (ex.: ``consumer price index``, ``unemployment``).
    limit : int
        Número de resultados (máximo 1000, padrão 100).
    order_by : str
        Campo de ordenação: ``search_rank``, ``series_id``, ``title``, ``frequency``,
        ``seasonal_adjustment``, ``last_updated``, ``observation_start``,
        ``observation_end``, ``popularity`` (padrão).
    sort_order : str
        ``asc`` ou ``desc`` (padrão).
    filter_variable : str | None
        Campo para filtro (ex.: ``frequency``).
    filter_value : str | None
        Valor do filtro (ex.: ``Monthly``).
    tag_names : str | None
        Tags separadas por ``;`` (ex.: ``annual;cpi``).
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    list[dict]
        Lista de dicionários de metadados de séries (mesma estrutura de ``metadados()``).

    Exemplos
    --------
    >>> series = fred.buscar("consumer price index", limit=20)
    >>> series = fred.buscar("unemployment", filter_variable="frequency", filter_value="Monthly")
    >>> series = fred.buscar("gdp", tag_names="annual;usa")
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()

    params: dict = {
        "search_text": texto,
        "api_key": key,
        "limit": limit,
        "order_by": order_by,
        "sort_order": sort_order,
    }
    if filter_variable:
        params["filter_variable"] = filter_variable
    if filter_value:
        params["filter_value"] = filter_value
    if tag_names:
        params["tag_names"] = tag_names

    try:
        url = _build_url("series/search", params)
        data = _request(session, url, timeout)
    finally:
        session.close()

    return data.get("seriess", [])


def categorias(
    category_id: int = 0,
    timeout: int = 30,
    api_key: str | None = None,
) -> dict:
    """
    Retorna informações de uma categoria FRED.

    ``category_id=0`` corresponde à categoria raiz (topo da hierarquia).

    Parâmetros
    ----------
    category_id : int
        ID da categoria FRED (padrão 0 = raiz).
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    dict
        Dicionário com ``id``, ``name``, ``parent_id``.

    Exemplos
    --------
    >>> raiz = fred.categorias()                # categoria raiz
    >>> macro = fred.categorias(125)            # Macroeconomics
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()
    try:
        url = _build_url("category", {"category_id": category_id, "api_key": key})
        data = _request(session, url, timeout)
    finally:
        session.close()

    cats = data.get("categories", [])
    if not cats:
        raise FredError(f"Categoria FRED {category_id} não encontrada.")
    return cats[0]


def series_categoria(
    category_id: int,
    limit: int = 100,
    timeout: int = 30,
    api_key: str | None = None,
) -> list[dict]:
    """
    Lista as séries pertencentes a uma categoria FRED.

    Parâmetros
    ----------
    category_id : int
        ID da categoria FRED.
    limit : int
        Número máximo de séries retornadas (padrão 100).
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    list[dict]
        Lista de metadados de séries (mesma estrutura de ``metadados()``).

    Exemplos
    --------
    >>> series = fred.series_categoria(125)   # séries da categoria Macroeconomics
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()
    try:
        url = _build_url("category/series", {"category_id": category_id, "api_key": key, "limit": limit})
        data = _request(session, url, timeout)
    finally:
        session.close()

    return data.get("seriess", [])


def tags(
    series_id: str,
    timeout: int = 30,
    api_key: str | None = None,
) -> list[dict]:
    """
    Retorna as tags associadas a uma série FRED.

    Parâmetros
    ----------
    series_id : str
        Código da série FRED.
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    list[dict]
        Lista de dicionários com ``name``, ``group_id``, ``notes``,
        ``created``, ``popularity``, ``series_count``.

    Exemplos
    --------
    >>> t = fred.tags("CPIAUCSL")
    >>> [x["name"] for x in t]
    ['bls', 'consumer price index', 'cpi', ...]
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()
    try:
        url = _build_url("series/tags", {"series_id": series_id, "api_key": key})
        data = _request(session, url, timeout)
    finally:
        session.close()

    return data.get("tags", [])


def release(
    release_id: int,
    timeout: int = 30,
    api_key: str | None = None,
) -> dict:
    """
    Retorna informações de um release FRED.

    Parâmetros
    ----------
    release_id : int
        ID do release FRED (ex.: 10 = Employment Situation).
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    dict
        Dicionário com ``id``, ``name``, ``press_release``, ``link``, ``notes``.

    Exemplos
    --------
    >>> r = fred.release(10)
    >>> r["name"]
    'Employment Situation'
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()
    try:
        url = _build_url("release", {"release_id": release_id, "api_key": key})
        data = _request(session, url, timeout)
    finally:
        session.close()

    releases = data.get("releases", [])
    if not releases:
        raise FredError(f"Release FRED {release_id} não encontrado.")
    return releases[0]


def series_release(
    release_id: int,
    limit: int = 100,
    timeout: int = 30,
    api_key: str | None = None,
) -> list[dict]:
    """
    Lista as séries pertencentes a um release FRED.

    Parâmetros
    ----------
    release_id : int
        ID do release FRED.
    limit : int
        Número máximo de séries (padrão 100).
    timeout : int
        Timeout em segundos (padrão 30).
    api_key : str | None
        Token FRED. Se None, usa TOKEN_FRED do ambiente.

    Retornos
    --------
    list[dict]
        Lista de metadados de séries.

    Exemplos
    --------
    >>> series = fred.series_release(10, limit=50)
    """
    key = api_key if api_key is not None else _get_token()
    session = _build_session()
    try:
        url = _build_url("release/series", {"release_id": release_id, "api_key": key, "limit": limit})
        data = _request(session, url, timeout)
    finally:
        session.close()

    return data.get("seriess", [])
