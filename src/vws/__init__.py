"""
A library for Vuforia Web Services.
"""

from ._version import get_versions
from .query import CloudRecoService
from .vws import VWS

__all__ = [
    'CloudRecoService',
    'VWS',
]

__version__ = get_versions()['version']  # type: ignore
del get_versions
