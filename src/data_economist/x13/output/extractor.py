"""
Extrai séries nomeadas do resultado X-13 (equivalente a series(m, key) no R).
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def get_series(model: Any, key: str) -> pd.Series | None:
    """
    Devolve uma série do resultado pelo nome (ex.: "final", "trend", "seats.trend").

    Chaves suportadas na v1:
      - "original" -> model.original
      - "final" -> model.final
      - "trend" -> model.trend
      - "irregular" -> model.irregular

    Outras chaves (ex.: "forecast.forecasts", "slidingspans.sfspans") podem ser
    adicionadas em fases posteriores quando o parser suportar mais tabelas.

    Devolve
    -------
    Series ou None se a chave não existir.

    Parâmetros
    ----------
    model : SeasonalResult
        Resultado de x13.seas().
    """
    key_lower = key.lower().strip()
    if key_lower == "original":
        return model.original
    if key_lower == "final":
        return model.final
    if key_lower in ("trend", "seats.trend"):
        return model.trend
    if key_lower in ("irregular", "seats.irregular"):
        return model.irregular
    return None
