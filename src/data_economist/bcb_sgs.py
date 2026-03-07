"""
Módulo BCB SGS — Dados do Sistema Gerenciador de Séries Temporais do Banco Central.

API: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
Exige dataInicial e dataFinal (DD/MM/YYYY); intervalo máximo 10 anos por requisição.

Uso::

    from data_economist import bcb_sgs
    dados = bcb_sgs.get(433)  # IPCA — série completa em JSON
"""
from __future__ import annotations

from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
_FORMATO = "json"
_MAX_ANOS_JANELA = 10
_RETRY_TOTAL = 4
_RETRY_BACKOFF = 0.8


class BCBSGSError(Exception):
    """Erro de comunicação/limite na API SGS do BCB."""


def _fmt(d: datetime) -> str:
    return d.strftime("%d/%m/%Y")


def _parse_data(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%d/%m/%Y")


def _parse_date_arg(value: str | datetime | None) -> datetime | None:
    """Converte date_init/date_end para datetime. Aceita 'YYYY-MM-DD' ou datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    s = value.strip()
    return datetime.strptime(s, "%Y-%m-%d")


def _build_session(retry_total: int = _RETRY_TOTAL, retry_backoff: float = _RETRY_BACKOFF) -> requests.Session:
    """
    Cria sessão HTTP com retry/backoff para erros transitórios.

    Retries em:
    - falhas de conexão/DNS
    - status 429 (limite de requisições)
    - status 5xx transitórios
    """
    session = requests.Session()
    retry = Retry(
        total=retry_total,
        connect=retry_total,
        read=retry_total,
        backoff_factor=retry_backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _request_json(
    session: requests.Session,
    url: str,
    timeout: int,
    *,
    contexto: str,
) -> tuple[int, list[dict] | dict]:
    """Faz GET resiliente e devolve (status_code, json)."""
    try:
        response = session.get(url, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        raise BCBSGSError(
            "Falha de conexão com a API do Banco Central (SGS). "
            "Pode ser erro transitório de DNS/rede ou limite temporário de acesso. "
            f"Contexto: {contexto}. URL: {url}"
        ) from exc

    # Limite de requisições / proteção
    if response.status_code == 429:
        raise BCBSGSError(
            "A API do Banco Central (SGS) devolveu HTTP 429 (limite de requisições). "
            "Aguarde alguns segundos/minutos e tente novamente com menor frequência de chamadas."
        )

    # Erro servidor após retries
    if response.status_code >= 500:
        raise BCBSGSError(
            f"A API do Banco Central (SGS) devolveu HTTP {response.status_code} "
            f"após tentativas de retry. Contexto: {contexto}. Tente novamente mais tarde."
        )

    if response.status_code == 404:
        return 404, []

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise BCBSGSError(
            f"Erro HTTP na API do Banco Central (SGS): {response.status_code}. "
            f"Contexto: {contexto}. URL: {url}"
        ) from exc

    try:
        return response.status_code, response.json()
    except ValueError as exc:
        raise BCBSGSError(
            "A API do Banco Central (SGS) devolveu JSON inválido. "
            f"Contexto: {contexto}. URL: {url}"
        ) from exc


def _obter_ultima_data(
    codigo: int | str,
    timeout: int = 30,
    session: requests.Session | None = None,
) -> datetime:
    """Obtém a data do último valor da série via endpoint ultimos/1."""
    url = f"{_BASE}.{codigo}/dados/ultimos/1?formato={_FORMATO}"
    own_session = session is None
    session = session or _build_session()
    _, data = _request_json(session, url, timeout, contexto=f"última data da série {codigo}")
    if own_session:
        session.close()

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Série SGS {codigo} inexistente ou sem dados: resposta inválida")
    ultimo = data[-1]
    data_str = ultimo.get("data")
    if not data_str:
        raise ValueError(f"Série SGS {codigo}: último registro sem campo 'data'")
    return _parse_data(data_str)


def _requisitar_janela(
    codigo: int | str,
    data_inicial: datetime,
    data_final: datetime,
    timeout: int = 30,
    session: requests.Session | None = None,
) -> list[dict]:
    """
    Requisita janela [dataInicial, dataFinal] (máx. 10 anos).

    Retorna lista de {data, valor}. Em 404 (sem dados no intervalo), devolve lista vazia.
    """
    url = (
        f"{_BASE}.{codigo}/dados?formato={_FORMATO}"
        f"&dataInicial={_fmt(data_inicial)}&dataFinal={_fmt(data_final)}"
    )
    own_session = session is None
    session = session or _build_session()
    status_code, data = _request_json(
        session,
        url,
        timeout,
        contexto=f"janela {_fmt(data_inicial)} a {_fmt(data_final)} (série {codigo})",
    )
    if own_session:
        session.close()

    if status_code == 404:
        return []
    if not isinstance(data, list):
        return []
    return data


def get(
    codigo: int | str,
    date_init: str | datetime | None = None,
    date_end: str | datetime | None = None,
    timeout: int = 30,
    retry_total: int = _RETRY_TOTAL,
    retry_backoff: float = _RETRY_BACKOFF,
) -> list[dict]:
    """
    Obtém a série SGS do BCB para o código dado, opcionalmente entre duas datas.

    - Sem datas: usa ``ultimos/1`` para a data do último valor e volta de 10 em 10 anos
      até 404/5xx ou ano < 1950.
    - Só date_init: obtém a data mais recente e volta de 10 em 10 anos até date_init.
    - Só date_end (date_init None): usa date_end como data final e volta de 10 em 10 anos
      até não obter resultado (404/5xx ou vazio).
    - date_init e date_end: requisita o intervalo [date_init, date_end] em janelas de 10 anos.

    Parâmetros
    ----------
    codigo : int | str
        Código da série no SGS (ex.: 433 para IPCA).
    date_init : str | datetime | None, opcional
        Data inicial ``YYYY-MM-DD``. Com date_end define o início do intervalo; sozinha
        limita até onde voltar (a data mais recente vem de ultimos/1).
    date_end : str | datetime | None, opcional
        Data final ``YYYY-MM-DD``. Sozinha: desta data para trás, de 10 em 10 anos, até
        não haver dados. Com date_init: fim do intervalo [date_init, date_end].
    timeout : int, opcional
        Timeout em segundos por requisição (default 30).
    retry_total : int, opcional
        Número de tentativas para erros transitórios (DNS/conexão/429/5xx). Default 4.
    retry_backoff : float, opcional
        Fator de backoff exponencial entre tentativas. Default 0.8.

    Retornos
    --------
    list[dict]
        Lista de registros com chaves ``data`` (DD/MM/YYYY) e ``valor`` (str),
        ordenada da data mais antiga para a mais recente.

    Exemplos
    --------
    >>> bcb_sgs.get(433)                          # série toda (último valor → para trás)
    >>> bcb_sgs.get(433, "2020-01-01")            # do início 2020 até o último valor
    >>> bcb_sgs.get(433, None, "2000-01-06")      # de 2000-01-06 para trás, 10 em 10 anos
    >>> bcb_sgs.get(433, "2020-01-01", "2025-01-01")  # só o intervalo 2020–2025
    """
    codigo = str(int(codigo))
    dt_init = _parse_date_arg(date_init)
    dt_end = _parse_date_arg(date_end)
    session = _build_session(retry_total=retry_total, retry_backoff=retry_backoff)

    try:
        # Data fim da série: última disponível (ultimos/1) ou date_end
        if dt_end is not None:
            data_fim = dt_end
        else:
            data_fim = _obter_ultima_data(codigo, timeout=timeout, session=session)

        resultado: list[dict] = []
        delta_10y = timedelta(days=_MAX_ANOS_JANELA * 365)

        while True:
            data_inicio = data_fim - delta_10y
            # Limitar ao date_init quando o usuário passou data inicial
            if dt_init is not None and data_inicio < dt_init:
                data_inicio = dt_init
            chunk = _requisitar_janela(
                codigo,
                data_inicio,
                data_fim,
                timeout=timeout,
                session=session,
            )
            if not chunk:
                break
            resultado = chunk + resultado
            data_fim = data_inicio - timedelta(days=1)
            # Parar se passamos da data inicial (intervalo limitado) ou limite de segurança
            if dt_init is not None and data_fim < dt_init:
                break
            if data_fim.year < 1950:
                break

        return resultado
    finally:
        session.close()
