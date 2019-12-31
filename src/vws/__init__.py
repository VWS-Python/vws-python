"""
A library for Vuforia Web Services.
"""

from pathlib import Path

from setuptools_scm import get_version

from .query import CloudRecoService
from .vws import VWS

__all__ = [
    'CloudRecoService',
    'VWS',
]

try:
    __version__ = get_version(root='..', relative_to=Path(__file__).parent)
except LookupError:  # pragma: no cover
    # When pkg_resources and git tags are not available,
    # for example in a PyInstaller binary,
    # we write the file ``_setuptools_scm_version.py`` on ``pip install``.
    _VERSION_FILE = Path(__file__).parent / '_setuptools_scm_version.txt'
    __version__ = _VERSION_FILE.read_text()
