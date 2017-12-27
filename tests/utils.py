"""
Utilities for tests.
"""


class VuforiaDatabaseKeys:
    """
    Credentials for VWS APIs.
    """

    def __init__(
        self,
        server_access_key: str,
        server_secret_key: str,
        client_access_key: str,
        client_secret_key: str,
        database_name: str,
    ) -> None:
        """
        Args:
            database_name: The name of a VWS target manager database name.
            server_access_key: A VWS server access key.
            server_secret_key: A VWS server secret key.
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.

        Attributes:
            database_name (str): The name of a VWS target manager database
                name.
            server_access_key (bytes): A VWS server access key.
            server_secret_key (bytes): A VWS server secret key.
            client_access_key (bytes): A VWS client access key.
            client_secret_key (bytes): A VWS client secret key.
        """
        self.server_access_key: bytes = bytes(
            server_access_key,
            encoding='utf-8',
        )
        self.server_secret_key: bytes = bytes(
            server_secret_key,
            encoding='utf-8',
        )
        self.client_access_key: bytes = bytes(
            client_access_key,
            encoding='utf-8',
        )
        self.client_secret_key: bytes = bytes(
            client_secret_key,
            encoding='utf-8',
        )
        self.database_name = database_name
