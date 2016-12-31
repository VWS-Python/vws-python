"""
Utilities for tests.
"""


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
