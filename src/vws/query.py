import io

class CloudRecoService:
    """
    An interface to Vuforia Web Services APIs.
    """

    def __init__(
        self,
        client_access_key: str,
        client_secret_key: str,
        # TODO - instead use vwq URL
        base_vws_url: str = 'https://vws.vuforia.com',
    ) -> None:
        """
        Args:
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.
            base_vws_url: The base URL for the VWS API.
        """
        self._client_access_key = client_access_key.encode()
        self._client_secret_key = client_secret_key.encode()
        self._base_vws_url = base_vws_url

    def query(
        self,
        image: io.BytesIO,
    ) -> str:
        """
        TODO docstring
        """
        pass
