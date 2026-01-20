"""Tutoring Dashboard package public exports.

Only expose modules that exist in this trimmed HTML-only version to avoid
import errors (e.g., when used as a package).
"""
from .config import Config, get_config
from .data_handler import SheetsDataHandler

__all__ = [
    "Config",
    "get_config",
    "SheetsDataHandler",
]
__version__ = "2.0.0"
