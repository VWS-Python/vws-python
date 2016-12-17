import pytest

import os


class VuforiaServerCredentials:
    """
    TODO
    """

    def __init__(self, access_key: str, secret_key: str) -> None:
        """
        TODO, Args, Ivar
        """
        self.access_key = bytes(access_key, encoding='utf-8')
        self.secret_key = bytes(secret_key, encoding='utf-8')


class FakeVuforiaAPI:
    """
    TODO
    """

    def __init__(self):
        self.access_key = 'blah_access_key'
        self.secret_key = 'blah_secret_key'


def vuforia_server_credentials(request) -> VuforiaServerCredentials:
    vuforia_server_access_key = os.getenv('VUFORIA_SERVER_ACCESS_KEY')
    vuforia_server_secret_key = os.getenv('VUFORIA_SERVER_SECRET_KEY')

    if not all([vuforia_server_access_key, vuforia_server_secret_key]):
        pytest.skip("Vuforia integration tests need creds")

    credentials = VuforiaServerCredentials(
        access_key=vuforia_server_access_key,
        secret_key=vuforia_server_secret_key,
    )
    return credentials
