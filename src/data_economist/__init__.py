"""
data_economist — Pacote Python para analistas e consultoria económica.

Funções para baixar dados de fontes económicas (BCE, Eurostat, IMF, etc.)
de forma fácil, para uso em análise e consultoria.

Autor: Uirá de Souza
"""

__version__ = "0.1.0"

from data_economist.ibge import get, url

__all__ = ["__version__", "get", "url", "ibge"]
