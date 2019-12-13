"""Setup script for VWS Python, a wrapper for Vuforia's Web Services APIs."""

from pathlib import Path
from setuptools import setup
from typing import List

import versioneer


def _get_dependencies(requirements_file: Path) -> List[str]:
    """
    Return requirements from a requirements file.

    This expects a requirements file with no ``--find-links`` lines.
    """
    lines = requirements_file.read_text().strip().split('\n')
    return [line for line in lines if not line.startswith('#')]


_DIRECT_REQUIRES = _get_dependencies(
    requirements_file=Path('requirements.txt'),
)

INSTALL_REQUIRES = _DIRECT_REQUIRES
DEV_REQUIRES = _get_dependencies(
    requirements_file=Path('dev-requirements.txt'),
)
PACKAGING_REQUIRES = _get_dependencies(
    requirements_file=Path('packaging-requirements.txt'),
)

setup(
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    install_requires=INSTALL_REQUIRES,
    extras_require={'dev': DEV_REQUIRES},
)
