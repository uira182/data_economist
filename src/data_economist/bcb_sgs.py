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

_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
_FORMATO = "json"
_MAX_ANOS_JANELA = 10


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


def _obter_ultima_data(codigo: int | str, timeout: int = 30) -> datetime:
    """Obtém a data do último valor da série via endpoint ultimos/1."""
    url = f"{_BASE}.{codigo}/dados/ultimos/1?formato={_FORMATO}"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    data = response.json()
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
) -> list[dict]:
    """Requisita uma janela [dataInicial, dataFinal] (máx. 10 anos). Retorna lista de {data, valor}.
    Em 404 (sem dados para o intervalo) ou 5xx (ex.: 502 Bad Gateway) retorna lista vazia e paramos a busca."""
    url = (
        f"{_BASE}.{codigo}/dados?formato={_FORMATO}"
        f"&dataInicial={_fmt(data_inicial)}&dataFinal={_fmt(data_final)}"
    )
    response = requests.get(url, timeout=timeout)
    # Sem dados para este intervalo (404) ou erro do servidor (502, etc.): retornar vazio
    if response.status_code == 404 or response.status_code >= 500:
        return []
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        return []
    return data


def get(
    codigo: int | str,
    date_init: str | datetime | None = None,
    date_end: str | datetime | None = None,
    timeout: int = 30,
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

    # Data fim da série: última disponível (ultimos/1) ou date_end
    if dt_end is not None:
        data_fim = dt_end
    else:
        data_fim = _obter_ultima_data(codigo, timeout=timeout)

    resultado: list[dict] = []
    delta_10y = timedelta(days=_MAX_ANOS_JANELA * 365)

    while True:
        data_inicio = data_fim - delta_10y
        # Limitar ao date_init quando o usuário passou data inicial
        if dt_init is not None and data_inicio < dt_init:
            data_inicio = dt_init
        chunk = _requisitar_janela(codigo, data_inicio, data_fim, timeout=timeout)
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
