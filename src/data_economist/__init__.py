"""
data_economist — Pacote Python para analistas e consultoria económica.

Funções para baixar dados de fontes económicas (BCE, Eurostat, IMF, etc.)
de forma fácil, para uso em análise e consultoria.

Autor: Uirá de Souza
"""

__version__ = "0.5.1"

import data_economist.ibge as ibge
from data_economist.ibge import get, url
import data_economist.bcb_sgs as bcb_sgs
import data_economist.comexstat as comexstat
import data_economist.eia as eia
import data_economist.x13 as x13

__all__ = ["__version__", "get", "url", "ibge", "bcb_sgs", "comexstat", "eia", "x13"]
