"""
Run tests and linters on Travis CI.
"""

import os
import subprocess
from pathlib import Path

import pytest


def run_test(test_filename: str) -> None:
    """
    Run pytest with a given filename.
    """
    path = Path('tests') / 'mock_vws' / test_filename
    pytest.main([
        '--exitfirst',
        str(path),
        '--cov=src',
        '--cov=tests',
    ])


if __name__ == '__main__':
    TEST_FILENAME = os.environ.get('TEST_FILENAME')
    if TEST_FILENAME:
        run_test(test_filename=TEST_FILENAME)
    else:
        subprocess.check_call(['make', 'lint'])
