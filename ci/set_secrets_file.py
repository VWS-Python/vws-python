"""
Move the right secrets file into place for Travis CI.
"""

import math
import os
import shutil
from pathlib import Path

CONCURRENT_BUILDS = 1


def move_secrets_file() -> None:
    """
    Move the right secrets file to the current directory.
    """
    branch = os.environ['TRAVIS_BRANCH']
    is_pr = os.environ['TRAVIS_PULL_REQUEST'] != 'false'
    is_master = branch == 'master'

    secrets_dir = Path('ci_secrets')

    if is_master and not is_pr:
        secrets_path = secrets_dir / 'vuforia_secrets_master.env'

    travis_build_number = float(os.environ['TRAVIS_BUILD_NUMBER'])
    travis_job_number = float(os.environ['TRAVIS_JOB_NUMBER'])
    travis_builder_number = math.ceil(
        (travis_job_number - travis_build_number) * 10
    )

    file_number = travis_builder_number % CONCURRENT_BUILDS
    secrets_path = secrets_dir / f'vuforia_secrets_{file_number}.env'
    shutil.copy(secrets_path, '.')


if __name__ == '__main__':
    move_secrets_file()
