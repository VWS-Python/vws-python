"""
Exceptions which do not map to errors at
https://library.vuforia.com/web-api/cloud-targets-web-services-api#result-codes
or simple errors given by the cloud recognition service.
"""


from .response import Response


class OopsAnErrorOccurredPossiblyBadName(Exception):
    """
    Exception raised when VWS returns an HTML page which says "Oops, an error
    occurred".

    This has been seen to happen when the given name includes a bad character.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response returned by Vuforia.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


class RequestEntityTooLarge(Exception):
    """
    Exception raised when the given image is too large.
    """


class TargetProcessingTimeout(Exception):
    """
    Exception raised when waiting for a target to be processed times out.
    """


class ServerError(Exception):  # pragma: no cover
    """
    Exception raised when VWS returns a server error.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response returned by Vuforia.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response
