"""
Move the right secrets file into place for Travis CI.
"""

import math
import os
import shutil
from pathlib import Path


def move_secrets_file() -> None:
    """
    Move the right secrets file to the current directory.
    """
    travis_build_number = float(os.environ['TRAVIS_BUILD_NUMBER'])
    travis_job_number = float(os.environ['TRAVIS_JOB_NUMBER'])
    travis_builder_number = math.ceil(
        (travis_job_number - travis_build_number) * 10
    )
    secrets_dir = Path('ci_secrets')
    secrets_path = secrets_dir / f'vuforia_secrets_{travis_builder_number}.env'
    shutil.copy(secrets_path, './vuforia_secrets.env')


if __name__ == '__main__':
    move_secrets_file()
