"""
Custom exceptions for Vuforia errors.

Generated with the script ``_generate_exceptions.py``.
"""

from requests import Response


class UnknownTarget(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'UnknownTarget'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response
