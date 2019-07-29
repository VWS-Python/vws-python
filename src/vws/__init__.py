"""
A library for Vuforia Web Services.
"""

from ._version import get_versions
from .vws import VWS
from .query import CloudRecoService

__all__ = [
    'CloudRecoService',
    'VWS',
]

__version__ = get_versions()['version']  # type: ignore
del get_versions
