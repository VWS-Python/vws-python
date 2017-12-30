"""
A fake implementation of the Vuforia Web Query API.

See
https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
"""

from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context


class MockVuforiaWebQueryAPI:
    """
    XXX
    """

    def __init__(
        self,
        client_access_key: str,
        server_secret_key: str,
        mock_target_api: MockVuforiaWebServicesAPI,
    ) -> None:
        """
        XXX
        """

    def query(
        self,
        request: _RequestObjectProxy,
        context: _Context,
    ) -> str:
        """
        XXX
        """
