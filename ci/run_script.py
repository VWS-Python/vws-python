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
    paths = [
        Path('tests') / 'mock_vws' / filename for filename in test_filenames
    ]
    result = pytest.main(
        [
            '-vvv',
            '--exitfirst',
            ' '.join(str(path) for path in paths),
            '--cov=src',
            '--cov=tests',
        ]
    )
    sys.exit(result)


if __name__ == '__main__':
    TEST_FILENAMES = os.environ.get('TEST_FILENAMES')
    if TEST_FILENAMES:
        run_test(test_filenames=TEST_FILENAMES.split(','))
    else:
        subprocess.check_call(['make', 'lint'])
