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
    num_secrets_files = len(list(secrets_dir.glob('*')))
    travis_max_concurrent_jobs = 5
    num_possible_concurrent_builds = min(
        num_secrets_files,
        travis_max_concurrent_jobs,
    )
    print("Possible concurrent builds: " + str(num_possible_concurrent_builds))
    print("Travis builder number: " + str(travis_builder_number))
    suffix = str(travis_builder_number % num_possible_concurrent_builds)
    secrets_path = secrets_dir / f'vuforia_secrets_{suffix}.env'
    shutil.copy(secrets_path, './vuforia_secrets.env')


if __name__ == '__main__':
    move_secrets_file()
