"""
Configuration, plugins and fixtures for `pytest`.
"""

import os

import pytest


class VuforiaServerCredentials:
    """
    Credentials for VWS APIs.
    """

    def __init__(self, access_key: str, secret_key: str) -> None:
        """
        Args:
            access_key: A VWS access key.
            secret_key: A VWS secret key.

        Attributes:
            access_key (bytes): A VWS access key.
            secret_key (bytes): A VWS secret key.
        """
        self.access_key = bytes(access_key, encoding='utf-8')  # type: bytes
        self.secret_key = bytes(secret_key, encoding='utf-8')  # type: bytes


@pytest.fixture()
def vuforia_server_credentials() -> VuforiaServerCredentials:
    """
    Return VWS credentials from environment variables.
    """
    vuforia_server_access_key = os.getenv('VUFORIA_SERVER_ACCESS_KEY')
    vuforia_server_secret_key = os.getenv('VUFORIA_SERVER_SECRET_KEY')

    if not all([vuforia_server_access_key, vuforia_server_secret_key]):
        pytest.skip(
            "Vuforia integration tests require secrets to be set in "
            "environment variables."
        )

    credentials = VuforiaServerCredentials(
        access_key=vuforia_server_access_key,
        secret_key=vuforia_server_secret_key,
    )
    return credentials
