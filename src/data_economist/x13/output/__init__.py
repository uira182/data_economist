"""
Output: extração de séries e resumo do resultado X-13.
"""

from .extractor import get_series
from .summary import summary

__all__ = ["get_series", "summary"]
