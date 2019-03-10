"""
A library for Vuforia Web Services.
"""

from ._version import get_versions
from .vws import VWS

__all__ = [
    'VWS',
]

__version__ = get_versions()['version']  # type: ignore
del get_versions
