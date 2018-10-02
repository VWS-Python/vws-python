"""
A library for Vuforia Web Services.
"""

from .vws import VWS

__all__ = [
    'VWS',
]

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
