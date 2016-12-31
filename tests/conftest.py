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
        access_key=os.environ['VUFORIA_SERVER_ACCESS_KEY'],
        secret_key=os.environ['VUFORIA_SERVER_SECRET_KEY'],
    )  # type: VuforiaServerCredentials
    return credentials
