"""
Base exceptions for errors returned by Vuforia Web Services or the Vuforia
Cloud Recognition Web API.
"""

from requests import Response


class CloudRecoException(Exception):
    """
    Base class for Vuforia Cloud Recognition Web API exceptions.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


class VWSException(Exception):
    """
    Base class for Vuforia Web Services errors.

    These errors are defined at
    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Interperete-VWS-API-Result-Codes.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response
