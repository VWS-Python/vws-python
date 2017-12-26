"""
Utilities for tests.
"""


class VuforiaDatabaseKeys:
    """
    Credentials for VWS APIs.
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        database_name: str,
    ) -> None:
        """
        Args:
            database_name: The name of a VWS target manager database name.
            access_key: A VWS access key.
            secret_key: A VWS secret key.

        Attributes:
            database_name (str): The name of a VWS target manager database
                name.
            access_key (bytes): A VWS access key.
            secret_key (bytes): A VWS secret key.
        """
        self.access_key: bytes = bytes(access_key, encoding='utf-8')
        self.secret_key: bytes = bytes(secret_key, encoding='utf-8')
        self.database_name = database_name
