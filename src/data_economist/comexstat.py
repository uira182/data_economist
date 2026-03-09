"""
Módulo ComexStat — Dados de comércio exterior (MDIC).

- **get(body):** POST /historical-data — body no padrão da documentação oficial.
- **get_general(flow, filter_key, filter_values, metrics):** GET /general — mapeamentos
  cuciGroup, chapter4.
- **get_filter(filter_id):** GET /filter/{id} — obtém um filtro guardado no site (ex.: 146862).
- **get_by_filter(filter_id_or_url):** Obtém o filtro pelo ID ou URL (ex. comexstat.mdic.gov.br/.../geral/146862)
  e consulta GET /general com esse filtro, devolvendo os dados.

Uso::

    from data_economist import comexstat
    resultado = comexstat.get({"flow": "export", ...})
    dados = comexstat.get_general("export", "cuciGroup", ["281b"], "metricFOB")
    # Filtro guardado no site (URL ou só o número)
    dados = comexstat.get_by_filter(146862)
    dados = comexstat.get_by_filter("https://comexstat.mdic.gov.br/pt/geral/146862")
"""
from __future__ import annotations

import json
import requests

# Evitar avisos SSL em ambientes onde a API usa certificado aceite apenas pelo browser
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

_API_HISTORICAL = "https://api-comexstat.mdic.gov.br/historical-data"
_API_GENERAL = "https://api-comexstat.mdic.gov.br/general"
_API_FILTER = "https://api-comexstat.mdic.gov.br/filter"

_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://comexstat.mdic.gov.br",
    "Referer": "https://comexstat.mdic.gov.br/",
}

# Mapeamentos filter key → (idInput, metadado para filterList)
_FILTER_METADATA = {
    "cuciGroup": (
        "noCuciPospt",
        {
            "id": "noCuciPospt",
            "text": "CUCI Grupo (produtos)",
            "route": "/pt/product-category/position",
            "type": "1",
            "group": "cuci",
            "groupText": "Classificação Uniforme para o Comércio Internacional (CUCI Ver.3)",
            "hint": "fieldsForm.general.noCuciPos.description",
            "placeholder": "CUCI Grupo",
        },
    ),
    "chapter4": (
        "noSh4pt",
        {
            "id": "noSh4pt",
            "text": "Posição (SH4)",
            "route": "/pt/harmonized-system/position",
            "type": "2",
            "group": "sh",
            "groupText": "Sistema Harmonizado (SH)",
            "hint": "fieldsForm.general.noSh4.description",
            "placeholder": "Posição (SH4)",
        },
    ),
}


def get(body: dict, timeout: int = 120) -> dict | list:
    """
    Consulta dados históricos do ComexStat (MDIC) via POST /historical-data.

    O **body** deve seguir o padrão da documentação oficial:
    - **flow:** ``"export"`` ou ``"import"``
    - **monthDetail:** bool (detalhamento mensal)
    - **period:** ``{"from": "YYYY-MM", "to": "YYYY-MM"}``
    - **filters:** lista de ``{"filter": "nome_do_filtro", "values": [...]}`` (ex.: state, country, ncm)
    - **details:** lista de dimensões para desagregação (ex.: ``["country", "state"]``)
    - **metrics:** lista de métricas (ex.: ``["metricFOB", "metricKG"]``)

    Parâmetros
    ----------
    body : dict
        Payload no formato da API ComexStat (documentação oficial).
    timeout : int, opcional
        Timeout da requisição em segundos (default 120).

    Retornos
    --------
    dict | list
        Resposta da API (geralmente um dict com chave ``data`` ou a lista de registos).
        Em erro HTTP, levanta ``requests.HTTPError``.

    Exemplos
    --------
    >>> body = {
    ...     "flow": "export",
    ...     "monthDetail": False,
    ...     "period": {"from": "2018-01", "to": "2018-01"},
    ...     "filters": [{"filter": "state", "values": [26]}],
    ...     "details": ["country", "state"],
    ...     "metrics": ["metricFOB", "metricKG"],
    ... }
    >>> resultado = comexstat.get(body)
    """
    response = requests.post(
        _API_HISTORICAL,
        headers=_HEADERS,
        json=body,
        timeout=timeout,
        verify=False,
    )
    response.raise_for_status()
    return response.json()


def _build_general_payload(
    flow: str,
    filter_id: str,
    filter_metadata: dict,
    filter_values: list,
    metric_fob: bool,
    metric_kg: bool,
    year_start: str = "1995",
    year_end: str = "2025",
) -> dict:
    """Monta o payload do parâmetro 'filter' para GET /general."""
    type_form = 1 if flow == "export" else 2
    return {
        "yearStart": year_start,
        "yearEnd": year_end,
        "typeForm": type_form,
        "typeOrder": 2,
        "filterList": [filter_metadata],
        "filterArray": [{"item": [str(v) for v in filter_values], "idInput": filter_id}],
        "rangeFilter": [],
        "detailDatabase": [],
        "monthDetail": True,
        "metricFOB": metric_fob,
        "metricKG": metric_kg,
        "metricStatistic": False,
        "metricFreight": False,
        "metricInsurance": False,
        "metricCIF": False,
        "monthStart": "01",
        "monthEnd": "12",
        "formQueue": "general",
        "langDefault": "pt",
        "monthStartName": "Janeiro",
        "monthEndName": "Dezembro",
    }


def get_general(
    flow: str,
    filter_key: str,
    filter_values: list,
    metrics: str = "metricFOB",
    timeout: int = 120,
) -> dict | list:
    """
    Consulta dados do ComexStat via GET /general.

    Usa os mapeamentos do notebook: cuciGroup (ex.: 281b, 672), chapter4 (ex.: 2603).
    Retorna a resposta da API (em geral dict com chave ``data`` contendo os registos).

    Parâmetros
    ----------
    flow : str
        ``"export"`` ou ``"import"``.
    filter_key : str
        Nome do filtro: ``"cuciGroup"`` ou ``"chapter4"``.
    filter_values : list
        Valores do filtro, ex. ``["281b"]``, ``["2603"]``.
    metrics : str
        ``"metricFOB"`` ou ``"metricKG"``.
    timeout : int
        Timeout em segundos (default 120).

    Retornos
    --------
    dict | list
        Resposta da API (geralmente ``{"data": [...], ...}``).

    Exemplos
    --------
    >>> dados = comexstat.get_general("export", "cuciGroup", ["281b"], "metricFOB")
    >>> dados = comexstat.get_general("import", "chapter4", ["2603"], "metricKG")
    """
    if filter_key not in _FILTER_METADATA:
        raise ValueError(f"filter_key deve ser um de {list(_FILTER_METADATA.keys())}")
    filter_id, filter_metadata = _FILTER_METADATA[filter_key]
    metric_fob = metrics == "metricFOB"
    metric_kg = metrics == "metricKG"
    payload = _build_general_payload(
        flow, filter_id, filter_metadata, filter_values, metric_fob, metric_kg
    )
    params = {"filter": json.dumps(payload)}
    response = requests.get(
        _API_GENERAL,
        headers=_HEADERS,
        params=params,
        timeout=timeout,
        verify=False,
    )
    response.raise_for_status()
    return response.json()


def _extrair_id_da_url(filter_id_or_url: str | int) -> str:
    """Se for URL (comexstat.../geral/146862), extrai o número; senão devolve como string."""
    if isinstance(filter_id_or_url, int):
        return str(filter_id_or_url)
    s = str(filter_id_or_url).strip()
    if "/geral/" in s or "/general/" in s:
        return s.rstrip("/").split("/")[-1]
    if s.isdigit():
        return s
    if "/" in s:
        return s.rstrip("/").split("/")[-1]
    return s


def get_filter(filter_id: str | int, timeout: int = 30) -> dict:
    """
    Obtém um filtro guardado no ComexStat (página "geral" com filtro criado pelo utilizador).

    GET https://api-comexstat.mdic.gov.br/filter/{id}
    A resposta inclui ``data.id``, ``data.filter`` (JSON em string, payload para /general)
    e ``data.createdAt``.

    Parâmetros
    ----------
    filter_id : str | int
        ID do filtro (ex.: 146862) ou URL completa (ex.: https://comexstat.mdic.gov.br/pt/geral/146862).
    timeout : int
        Timeout em segundos (default 30).

    Retornos
    --------
    dict
        Resposta da API: ``{"data": {"id": ..., "filter": "<JSON string>", "createdAt": ...}, "success": ...}``.
    """
    id_str = _extrair_id_da_url(filter_id)
    url = f"{_API_FILTER}/{id_str}"
    response = requests.get(url, headers=_HEADERS, timeout=timeout, verify=False)
    response.raise_for_status()
    return response.json()


def get_by_filter(filter_id_or_url: str | int, timeout: int = 120) -> dict | list:
    """
    Obtém os dados usando um filtro guardado no site ComexStat.

    1. Obtém o filtro via GET /filter/{id} (o ID pode ser extraído da URL, ex. .../geral/146862).
    2. Usa o payload em ``data.filter`` para GET /general e devolve o resultado.

    Parâmetros
    ----------
    filter_id_or_url : str | int
        ID do filtro (ex.: 146862) ou URL da página (ex.: https://comexstat.mdic.gov.br/pt/geral/146862).
    timeout : int
        Timeout em segundos para cada requisição (default 120).

    Retornos
    --------
    dict | list
        Resposta de GET /general (em geral ``{"data": {"list": [...]}, "success": true, ...}``).

    Exemplos
    --------
    >>> dados = comexstat.get_by_filter(146862)
    >>> dados = comexstat.get_by_filter("https://comexstat.mdic.gov.br/pt/geral/146862")
    >>> registos = dados["data"]["list"]
    """
    resp_filter = get_filter(filter_id_or_url, timeout=min(30, timeout))
    filter_str = resp_filter.get("data", {}).get("filter")
    if not filter_str:
        raise ValueError("Resposta do /filter não contém data.filter")
    try:
        payload = json.loads(filter_str)
    except json.JSONDecodeError:
        payload = json.loads(filter_str.replace("\\u0022", '"'))
    payload_str = json.dumps(payload)
    params = {"filter": payload_str}
    response = requests.get(
        _API_GENERAL,
        headers=_HEADERS,
        params=params,
        timeout=timeout,
        verify=False,
    )
    response.raise_for_status()
    return response.json()
