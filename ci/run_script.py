"""
Run tests and linters on Travis CI.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_test(ci_pattern: str) -> None:
    """
    Run pytest with a given filename.
    """
    path = Path('tests') / 'mock_vws' / ci_pattern
    result = pytest.main(
        [
            '-vvv',
            '--exitfirst',
            str(path),
            '--cov=src',
            '--cov=tests',
        ],
    )
    sys.exit(result)


if __name__ == '__main__':
    CI_PATTERN = os.environ.get('CI_PATTERN')
    if CI_PATTERN:
        run_test(ci_pattern=CI_PATTERN)
    else:
        subprocess.check_call(['make', 'lint'])
