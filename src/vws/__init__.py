"""
A library for Vuforia Web Services.
"""

from pathlib import Path

from .query import CloudRecoService
from .vws import VWS

__all__ = [
    'CloudRecoService',
    'VWS',
]
