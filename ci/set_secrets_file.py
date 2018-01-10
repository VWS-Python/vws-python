"""
Move the right secrets file into place for Travis CI.
"""

import os
import shutil
from pathlib import Path


def move_secrets_file() -> None:
    """
    Move the right secrets file to the current directory.
    """
    print(os.environ)
    branch = os.environ['TRAVIS_BRANCH']
    is_pr = os.environ['TRAVIS_PULL_REQUEST'] != 'false'
    is_master = branch == 'master'

    secrets_dir = Path('ci_secrets')

    if is_master and not is_pr:
        secrets_path = secrets_dir / 'vuforia_secrets_master.env'

    secrets_path = secrets_dir / 'vuforia_secrets.env'
    shutil.copy(secrets_path, '.')


if __name__ == '__main__':
    move_secrets_file()
