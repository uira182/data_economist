"""
Conversão de frequência de séries temporais.

Suporta:
- Alta para baixa frequência (ex.: diário para mensal): agregação por média, soma,
  primeiro, último, máximo ou mínimo valor do período.
- Baixa para alta frequência (ex.: mensal para diário): interpolação linear,
  quadrática, cúbica, forward-fill (constante), pchip ou spline.

Entrada esperada: pd.Series com DatetimeIndex.
"""

from __future__ import annotations

import pandas as pd

# Métodos de agregação (alta para baixa frequência)
_METODOS_AGREGACAO = {"mean", "sum", "first", "last", "max", "min"}

# Métodos de interpolação (baixa para alta frequência)
_METODOS_INTERPOLACAO = {"linear", "quadratic", "cubic", "ffill", "pchip", "spline"}

_TODOS_METODOS = _METODOS_AGREGACAO | _METODOS_INTERPOLACAO


def _freq_em_dias(freq_str: str) -> float:
    """Converte string de frequência em duração aproximada em dias para comparação."""
    f = freq_str.upper().lstrip("0123456789")
    tabela = {
        "T": 1 / 1440,    # minutal
        "H": 1 / 24,      # horário
        "D": 1,
        "B": 1,            # dia útil ~ 1 dia
        "W": 7,
        "SME": 15,         # semi-mensal
        "ME": 30,
        "MS": 30,
        "QE": 91,
        "QS": 91,
        "YE": 365,
        "YS": 365,
        "A": 365,
        "Y": 365,
        "Q": 91,
        "M": 30,
    }
    for key in sorted(tabela.keys(), key=len, reverse=True):
        if f.startswith(key):
            return tabela[key]
    return 30  # fallback mensal


def _detectar_direcao(serie: pd.Series, freq_destino: str) -> str:
    """
    Detecta se a conversão é de alta para baixa frequência ("agregar")
    ou de baixa para alta ("interpolar").
    """
    # Usar freqstr (mais confiável que str(freq) em pandas recente)
    freq_str_origem = getattr(serie.index, "freqstr", None)
    if freq_str_origem is None:
        # Sem freq no índice: estimar pela distância média entre observações
        if len(serie) < 2:
            return "agregar"
        delta = (serie.index[-1] - serie.index[0]).days / max(len(serie) - 1, 1)
        dias_origem = delta
    else:
        freq_str_origem = freq_str_origem.upper().split("-")[0]
        dias_origem = _freq_em_dias(freq_str_origem)

    dias_destino = _freq_em_dias(freq_destino.upper().split("-")[0])

    if dias_destino >= dias_origem * 1.5:
        return "agregar"
    return "interpolar"


def para_frequencia(
    serie: pd.Series,
    freq: str,
    metodo: str = "mean",
) -> pd.Series:
    """
    Converte a série para uma nova frequência.

    Alta para baixa frequência (ex.: diário para mensal, mensal para anual):
        Agrega os valores do período usando o método especificado.
        Métodos disponíveis: "mean", "sum", "first", "last", "max", "min".

    Baixa para alta frequência (ex.: mensal para diário, trimestral para mensal):
        Interpola os valores para preencher a nova grade de datas.
        Métodos disponíveis: "linear", "quadratic", "cubic",
        "ffill" (constante/forward-fill), "pchip", "spline".

    Parâmetros
    ----------
    serie : pd.Series
        Série temporal com DatetimeIndex.
    freq : str
        Frequência de destino no formato pandas (ex.: "ME", "QE", "YE", "D", "W").
    metodo : str
        Método de agregação ou interpolação (padrão "mean").
        Para alta para baixa: "mean", "sum", "first", "last", "max", "min".
        Para baixa para alta: "linear", "quadratic", "cubic", "ffill", "pchip", "spline".

    Retorna
    -------
    pd.Series
        Série na nova frequência.

    Exemplos
    --------
    Mensal para trimestral (média):
        trimestral = para_frequencia(serie_mensal, freq="QE", metodo="mean")

    Mensal para diário (interpolação linear):
        diario = para_frequencia(serie_mensal, freq="D", metodo="linear")
    """
    if not isinstance(serie.index, pd.DatetimeIndex):
        raise ValueError(
            "para_frequencia(): a série deve ter DatetimeIndex. "
            f"Tipo atual: {type(serie.index).__name__}"
        )
    if len(serie) < 2:
        raise ValueError("para_frequencia(): a série precisa de ao menos 2 observações.")
    if metodo not in _TODOS_METODOS:
        raise ValueError(
            f"para_frequencia(): metodo '{metodo}' inválido. "
            f"Use um de: {sorted(_TODOS_METODOS)}"
        )

    direcao = _detectar_direcao(serie, freq)

    # Se o método é de agregação, forçar direção "agregar" independente da detecção
    if metodo in _METODOS_AGREGACAO:
        direcao = "agregar"
    # Se o método é de interpolação, forçar "interpolar"
    elif metodo in _METODOS_INTERPOLACAO:
        direcao = "interpolar"

    if direcao == "agregar":
        return _agregar(serie, freq, metodo)
    return _interpolar(serie, freq, metodo)


def _agregar(serie: pd.Series, freq: str, metodo: str) -> pd.Series:
    """Agrega a série para frequência menor (mais espaçada)."""
    resampler = serie.resample(freq)

    if metodo == "mean":
        resultado = resampler.mean()
    elif metodo == "sum":
        resultado = resampler.sum()
    elif metodo == "first":
        resultado = resampler.first()
    elif metodo == "last":
        resultado = resampler.last()
    elif metodo == "max":
        resultado = resampler.max()
    elif metodo == "min":
        resultado = resampler.min()
    else:
        # metodo de interpolação passado para direção de agregação — usa mean como fallback
        resultado = resampler.mean()

    return resultado.dropna()


def _interpolar(serie: pd.Series, freq: str, metodo: str) -> pd.Series:
    """Interpola a série para frequência maior (mais densa)."""
    # Reindexar para a nova grade e interpolar
    nova_grade = pd.date_range(
        start=serie.index.min(),
        end=serie.index.max(),
        freq=freq,
    )

    # Combinar índice original com nova grade para preservar os pontos conhecidos
    idx_combinado = serie.index.union(nova_grade)
    serie_reindexada = serie.reindex(idx_combinado)

    if metodo == "ffill":
        interpolada = serie_reindexada.ffill()
    else:
        interpolada = serie_reindexada.interpolate(method=metodo)

    # Retornar apenas os pontos da nova grade
    return interpolada.reindex(nova_grade)
