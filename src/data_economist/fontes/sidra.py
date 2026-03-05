"""
API SIDRA do IBGE — Sistema IBGE de Recuperação Automática.

Documentação: https://apisidra.ibge.gov.br

Para uso com detecção automática de formato, use o módulo ibge::

    from data_economist import ibge
    dados = ibge.url(url)   # ou ibge.url([url1, url2]) para várias URLs
"""

from data_economist.ibge import get, url

__all__ = ["get", "url"]
