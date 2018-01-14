"""
Run tests and linters on Travis CI.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest


def run_test(test_filenames: List[str]) -> None:
    """
    Run pytest with a given filename.
    """
    for filename in test_filenames:
        path = Path('tests') / 'mock_vws' / filename
        result = pytest.main(
            [
                '-vvv',
                '--exitfirst',
                str(path),
                '--cov=src',
                '--cov=tests',
            ]
        )
        if result:
            sys.exit(result)


if __name__ == '__main__':
    TEST_FILENAMES = os.environ.get('TEST_FILENAMES')
    if TEST_FILENAMES:
        run_test(test_filenames=TEST_FILENAMES.split(','))
    else:
        subprocess.check_call(['make', 'lint'])
