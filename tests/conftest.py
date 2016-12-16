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


@pytest.fixture()
def vuforia_server_credentials() -> VuforiaServerCredentials:
    # This should be parametrized and either use credentials
    # or mock the Vuforia instance
    # If the credentials aren't available in the environment,
    # then skip the real Vuforia test
    # Have a marker to skip these tests as they use resources and the internet
    #
    # Also change the:
    #   README
    #   TravisCI file
    #   Secret env file
    #   Secret env template file
    #
    # To handle the new env vars
    # Finalizer: Delete all targets
    vuforia_server_access_key = os.getenv('VUFORIA_SERVER_ACCESS_KEY')
    vuforia_server_secret_key = os.getenv('VUFORIA_SERVER_SECRET_KEY')
    if not all([vuforia_server_access_key, vuforia_server_secret_key]):
        pytest.skip("Vuforia integration tests need creds")

    credentials = VuforiaServerCredentials(
        access_key=vuforia_server_access_key,
        secret_key=vuforia_server_secret_key,
    )
    return credentials

# vuforia = VuforiaMock()
# vuforia = Vuforia(access_key='a', secret_key='a')
