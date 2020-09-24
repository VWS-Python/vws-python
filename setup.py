"""Setup script for VWS Python, a wrapper for Vuforia's Web Services APIs."""

from pathlib import Path
from typing import List

from setuptools import setup


def _get_dependencies(requirements_file: Path) -> List[str]:
    """
    Return requirements from a requirements file.

    This expects a requirements file with no ``--find-links`` lines.
    """
    lines = requirements_file.read_text().strip().split('\n')
    return [line for line in lines if not line.startswith('#')]


INSTALL_REQUIRES = _get_dependencies(
    requirements_file=Path('requirements.txt'),
)

DEV_REQUIRES = _get_dependencies(
    requirements_file=Path('dev-requirements.txt'),
)

SETUP_REQUIRES = _get_dependencies(
    requirements_file=Path('setup-requirements.txt'),
)

setup(
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require={'dev': DEV_REQUIRES},
    python_requires='>=3',
)
