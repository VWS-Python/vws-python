"""
Exceptions which do not map to errors at
https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#result-codes
or simple errors given by the cloud recognition service.
"""

from beartype import beartype

from vws.types import Response


@beartype
class OopsAnErrorOccurredPossiblyBadNameError(Exception):
    """Exception raised when VWS returns an HTML page which says "Oops, an
    error occurred".

    This has been seen to happen when the given name includes a bad
    character.
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


@beartype
class RequestEntityTooLargeError(Exception):
    """
    Exception raised when the given image is too large.
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


@beartype
class TargetProcessingTimeoutError(Exception):
    """
    Exception raised when waiting for a target to be processed times out.
    """


@beartype
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
