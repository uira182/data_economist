"""
Módulo EIA — U.S. Energy Information Administration (dados energéticos).

Requer token de API em variável de ambiente TOKEN_EIA (ex.: no ficheiro .env).
Registo do token: https://www.eia.gov/opendata/register.php

Uso::

    # No .env: TOKEN_EIA=seu_token
    from data_economist import eia
    # Por URL completa
    lista = eia.get_data("https://api.eia.gov/v2/steo/data/?frequency=monthly&...")
    # Por parâmetros (STEO ou Petroleum)
    dados = eia.get_steo("PATC_WORLD", "monthly")
    dados = eia.get_petroleum("pri/spt", "EER_EPMRU_PF4_RGC_DPG", "daily")
    # Mapeamento setor + frequência: eia.SERIES_STEO, eia.SERIES_PETROLEUM
"""
from __future__ import annotations

import os
from urllib.parse import urlencode

import requests

_BASE = "https://api.eia.gov/v2"

# ---------------------------------------------------------------------------
# Mapeamento setor × frequência → séries
# Usar com get_steo(series_id, frequency) ou get_petroleum(route, series, frequency)
# ---------------------------------------------------------------------------
SERIES_STEO: dict[str, list[str]] = {
    "petroleo_monthly": ["PASC_OECD_T3", "PATC_WORLD", "PAPR_WORLD", "PAPR_OPEC"],
    "quimicos_monthly": ["NGHHUUS", "HSTCXUS", "MVVMPUS", "ZO322IUS"],
    "quimicos_quarterly": ["NGHHUUS", "HSTCXUS", "MVVMPUS"],
    "quimicos_annual": ["NGHHUUS", "HSTCXUS", "MVVMPUS"],
    "min_sid_monthly": ["ZOTOIUS"],
}
"""Séries STEO por setor e frequência. Chave = \"setor_frequency\" (ex.: petroleo_monthly)."""

SERIES_PETROLEUM: dict[str, list[tuple[str, str]]] = {
    "petroleo_weekly": [
        ("cons/wpsup", "WGFUPUS2"),
        ("pnp/wprodrb", "W_EPM0F_YPR_NUS_MBBLD"),
        ("sum/sndw", "WGTSTUS1"),
        ("pnp/wiup", "WPULEUS3"),
        ("sum/sndw", "WRPUPUS2"),
        ("cons/wpsup", "WDIUPUS2"),
        ("pnp/wprodrb", "WDIRPUS2"),
        ("sum/sndw", "WDISTUS1"),
        ("move/wkly", "WGTIMUS2"),
        ("move/wkly", "WCRIMUS2"),
        ("sum/sndw", "W_EPOOXE_YOP_NUS_MBBLD"),
    ],
    "petroleo_daily": [
        ("pri/spt", "EER_EPMRU_PF4_RGC_DPG"),
        ("pri/spt", "EER_EPMRR_PF4_Y05LA_DPG"),
        ("pri/spt", "EER_EPD2F_PF4_Y35NY_DPG"),
        ("pri/spt", "EER_EPD2DXL0_PF4_RGC_DPG"),
    ],
}
"""Séries Petroleum por setor e frequência. Chave = \"setor_frequency\". Valor = lista de (route, series)."""

# Links para mensagens de erro (documentação e registo do token)
_EIA_REGISTER_URL = "https://www.eia.gov/opendata/register.php"
_EIA_DOC_URL = "https://www.eia.gov/opendata/documentation.php"
_MSG_ENV_OU_TOKEN = (
    "Documentação EIA (registo de token e uso da API): "
    f"{_EIA_DOC_URL} | Registo do token: {_EIA_REGISTER_URL}"
)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _get_token() -> str:
    """Obtém o token EIA de TOKEN_EIA no ambiente. Levanta ValueError se faltar."""
    _load_env()
    token = os.environ.get("TOKEN_EIA") or os.environ.get("EIA_API_KEY")
    if not token or not str(token).strip():
        raise ValueError(
            "Falta configurar o token EIA. Crie ou edite o ficheiro .env na raiz do projeto "
            "e adicione: TOKEN_EIA=seu_token (obtenha o token no registo abaixo). "
            f"{_MSG_ENV_OU_TOKEN}"
        )
    return str(token).strip()


def _add_api_key(url: str, api_key: str) -> str:
    """Adiciona api_key à URL como parâmetro de query."""
    if "api_key=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}api_key={api_key}"


def get(url: str, timeout: int = 30, api_key: str | None = None) -> dict:
    """
    Consulta a API EIA v2 com uma URL completa (à qual é adicionado o api_key).

    O token é lido de TOKEN_EIA no ambiente (ou do ficheiro .env, se existir e
    python-dotenv estiver instalado). Pode ser sobrescrito com o parâmetro api_key.

    Parâmetros
    ----------
    url : str
        URL completa do endpoint EIA (ex.: https://api.eia.gov/v2/steo/data/?frequency=monthly&...).
        O parâmetro api_key será adicionado automaticamente se não estiver presente.
    timeout : int, opcional
        Timeout da requisição em segundos (default 30).
    api_key : str ou None, opcional
        Token de API. Se None, usa TOKEN_EIA do ambiente.

    Retornos
    --------
    dict
        Resposta JSON da API (estrutura típica: ``{"response": {"data": [...], ...}}``).

    Raises
    ------
    ValueError
        Se TOKEN_EIA não estiver definido e api_key não for passado.
    requests.HTTPError
        Em falha HTTP (4xx/5xx).

    Exemplos
    --------
    >>> # .env: TOKEN_EIA=seu_token
    >>> resp = eia.get("https://api.eia.gov/v2/steo/data/?frequency=monthly&data[0]=value&facets[seriesId][]=PATC_WORLD&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000")
    >>> "response" in resp
    True
    """
    key = api_key if api_key is not None else _get_token()
    url_with_key = _add_api_key(url, key)
    response = requests.get(url_with_key, timeout=timeout)

    if response.status_code in (401, 403):
        raise ValueError(
            "Token EIA inválido ou não autorizado. Verifique se o ficheiro .env existe, "
            "se TOKEN_EIA está correto e se o token foi obtido no registo da EIA. "
            f"{_MSG_ENV_OU_TOKEN}"
        )
    response.raise_for_status()

    data = response.json()
    # Algumas respostas de erro da API vêm com 200 e campo "error" no JSON
    if isinstance(data, dict) and data.get("error"):
        err = data.get("error")
        raise ValueError(
            f"Resposta da API EIA indicou erro: {err}. "
            "Confirme que o token no .env (TOKEN_EIA) está correto. "
            f"{_MSG_ENV_OU_TOKEN}"
        )
    return data


def get_data(url: str, timeout: int = 30, api_key: str | None = None) -> list[dict]:
    """
    Consulta a API EIA v2 e devolve apenas a lista de registos (response.response.data).

    Parâmetros
    ----------
    url : str
        URL completa do endpoint EIA (o api_key é adicionado automaticamente).
    timeout : int, opcional
        Timeout em segundos (default 30).
    api_key : str ou None, opcional
        Token de API; se None, usa TOKEN_EIA do ambiente.

    Retornos
    --------
    list[dict]
        Lista de registos (cada um com ``period``, ``value`` e identificador de série).
        Lista vazia se a API não devolver dados.

    Exemplos
    --------
    >>> dados = eia.get_data("https://api.eia.gov/v2/steo/data/?frequency=monthly&data[0]=value&facets[seriesId][]=PATC_WORLD&...")
    >>> for r in dados[:3]:
    ...     print(r.get("period"), r.get("value"))
    """
    resp = get(url, timeout=timeout, api_key=api_key)
    data = resp.get("response", {}).get("data")
    if not isinstance(data, list):
        return []
    return data


def _build_steo_url(
    series_id: str,
    frequency: str,
    offset: int = 0,
    length: int = 5000,
    sort_desc: bool = True,
) -> str:
    """Monta a URL do endpoint STEO (Short-Term Energy Outlook)."""
    params: dict[str, str | int] = {
        "frequency": frequency,
        "data[0]": "value",
        "facets[seriesId][]": series_id,
        "offset": offset,
        "length": length,
    }
    if sort_desc:
        params["sort[0][column]"] = "period"
        params["sort[0][direction]"] = "desc"
    return f"{_BASE}/steo/data/?{urlencode(params)}"


def _build_petroleum_url(
    route: str,
    series: str,
    frequency: str,
    offset: int = 0,
    length: int = 5000,
    sort_desc: bool = True,
) -> str:
    """Monta a URL do endpoint Petroleum (route = ex. cons/wpsup, pri/spt)."""
    params: dict[str, str | int] = {
        "frequency": frequency,
        "data[0]": "value",
        "facets[series][]": series,
        "offset": offset,
        "length": length,
    }
    if sort_desc:
        params["sort[0][column]"] = "period"
        params["sort[0][direction]"] = "desc"
    return f"{_BASE}/petroleum/{route}/data/?{urlencode(params)}"


def get_steo(
    series_id: str,
    frequency: str = "monthly",
    offset: int = 0,
    length: int = 5000,
    timeout: int = 30,
    api_key: str | None = None,
) -> list[dict]:
    """
    Obtém dados do endpoint **STEO** (Short-Term Energy Outlook) por série e frequência.

    Equivalente às URLs do tipo ``/v2/steo/data/?frequency=monthly&facets[seriesId][]=PATC_WORLD&...``
    usadas no mapeamento (petróleo mensal, químicos mensal/trimestral/anual, min_sid).

    Parâmetros
    ----------
    series_id : str
        Identificador da série STEO (ex.: ``PATC_WORLD``, ``NGHHUUS``, ``ZOTOIUS``).
    frequency : str
        Frequência: ``monthly``, ``quarterly`` ou ``annual``.
    offset : int
        Deslocamento na paginação (default 0).
    length : int
        Número de registos (default 5000).
    timeout : int
        Timeout em segundos (default 30).
    api_key : str ou None
        Token EIA; se None, usa TOKEN_EIA do ambiente.

    Retornos
    --------
    list[dict]
        Lista de registos (``period``, ``value``, ``seriesId``, etc.).

    Exemplos
    --------
    >>> dados = eia.get_steo("PATC_WORLD", "monthly")
    >>> dados = eia.get_steo("NGHHUUS", "quarterly", length=100)
    >>> # Séries: eia.SERIES_STEO["petroleo_monthly"]
    """
    url = _build_steo_url(series_id, frequency, offset=offset, length=length)
    return get_data(url, timeout=timeout, api_key=api_key)


def get_petroleum(
    route: str,
    series: str,
    frequency: str,
    offset: int = 0,
    length: int = 5000,
    timeout: int = 30,
    api_key: str | None = None,
) -> list[dict]:
    """
    Obtém dados do endpoint **Petroleum** por rota, série e frequência.

    Equivalente às URLs do tipo ``/v2/petroleum/cons/wpsup/data/?frequency=weekly&facets[series][]=WGFUPUS2&...``
    usadas no mapeamento (petróleo semanal e diário).

    Parâmetros
    ----------
    route : str
        Sub-rota do petroleum (ex.: ``cons/wpsup``, ``sum/sndw``, ``pri/spt``, ``pnp/wprodrb``, ``pnp/wiup``, ``move/wkly``).
    series : str
        Código da série (ex.: ``WGFUPUS2``, ``EER_EPMRU_PF4_RGC_DPG``).
    frequency : str
        Frequência: ``weekly`` ou ``daily`` (conforme o endpoint).
    offset : int
        Deslocamento na paginação (default 0).
    length : int
        Número de registos (default 5000).
    timeout : int
        Timeout em segundos (default 30).
    api_key : str ou None
        Token EIA; se None, usa TOKEN_EIA do ambiente.

    Retornos
    --------
    list[dict]
        Lista de registos (``period``, ``value``, ``series``, etc.).

    Exemplos
    --------
    >>> dados = eia.get_petroleum("pri/spt", "EER_EPMRU_PF4_RGC_DPG", "daily")
    >>> dados = eia.get_petroleum("cons/wpsup", "WGFUPUS2", "weekly")
    >>> # Pares (route, series): eia.SERIES_PETROLEUM["petroleo_weekly"]
    """
    url = _build_petroleum_url(route, series, frequency, offset=offset, length=length)
    return get_data(url, timeout=timeout, api_key=api_key)


def get_by_landing(
    sector: str,
    frequency: str,
    timeout: int = 30,
    api_key: str | None = None,
) -> dict[str, list[dict]]:
    """
    Obtém todos os dados do mapeamento para um **setor** e **frequência**.

    Usa os dicionários ``SERIES_STEO`` e ``SERIES_PETROLEUM``. Devolve um dicionário
    em que cada chave é um identificador da série e o valor é a lista de registos.

    Parâmetros
    ----------
    sector : str
        Setor: ``petroleo``, ``quimicos`` ou ``min_sid``.
    frequency : str
        Frequência: ``monthly``, ``quarterly``, ``annual`` (STEO) ou ``weekly``, ``daily`` (Petroleum).
    timeout : int
        Timeout por requisição (default 30).
    api_key : str ou None
        Token EIA; se None, usa TOKEN_EIA do ambiente.

    Retornos
    --------
    dict[str, list[dict]]
        Chave = identificador da série (seriesId ou series); valor = lista de registos.

    Exemplos
    --------
    >>> tudo = eia.get_by_landing("petroleo", "monthly")
    >>> # tudo["PATC_WORLD"], tudo["PAPR_OPEC"], ...
    >>> tudo = eia.get_by_landing("petroleo", "weekly")
    >>> tudo = eia.get_by_landing("quimicos", "quarterly")
    """
    key = f"{sector}_{frequency}"
    result: dict[str, list[dict]] = {}

    if key in SERIES_STEO:
        for series_id in SERIES_STEO[key]:
            data = get_steo(series_id, frequency, timeout=timeout, api_key=api_key)
            result[series_id] = data

    if key in SERIES_PETROLEUM:
        for route, series in SERIES_PETROLEUM[key]:
            data = get_petroleum(route, series, frequency, timeout=timeout, api_key=api_key)
            # Chave única para rotas com várias séries
            label = f"{route}_{series}" if any(s != series for _, s in SERIES_PETROLEUM[key]) else series
            result[label] = data

    return result
