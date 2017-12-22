"""
Configuration, plugins and fixtures for `pytest`.
"""

import os

import pytest

from tests.utils import VuforiaServerCredentials


@pytest.fixture()
def vuforia_server_credentials() -> VuforiaServerCredentials:
    """
    Return VWS credentials from environment variables.
    """
    credentials = VuforiaServerCredentials(
        database_name=os.environ['VUFORIA_TARGET_MANAGER_DATABASE_NAME'],
        access_key=os.environ['VUFORIA_SERVER_ACCESS_KEY'],
        secret_key=os.environ['VUFORIA_SERVER_SECRET_KEY'],
    )  # type: VuforiaServerCredentials
    return credentials


@pytest.fixture()
def inactive_server_credentials() -> VuforiaServerCredentials:
    """
    Return VWS credentials for an inactive project from environment variables.
    """
    credentials = VuforiaServerCredentials(
        database_name=os.
        environ['INACTIVE_VUFORIA_TARGET_MANAGER_DATABASE_NAME'],
        access_key=os.environ['INACTIVE_VUFORIA_SERVER_ACCESS_KEY'],
        secret_key=os.environ['INACTIVE_VUFORIA_SERVER_SECRET_KEY'],
    )  # type: VuforiaServerCredentials
    return credentials
