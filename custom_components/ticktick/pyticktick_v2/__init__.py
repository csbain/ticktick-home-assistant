"""Vendored pyticktick v2 API client for TickTick Home Assistant integration.

This is a streamlined version of pyticktick that only includes v2 API support.
Based on pyticktick v0.3.0 by Seb Pretzer (MIT License).

Original: https://pyticktick.pretzer.io/
"""

from .api.client import Client
from .api.settings import Settings

__all__ = ["Client", "Settings"]
__version__ = "0.3.0-vendored"
