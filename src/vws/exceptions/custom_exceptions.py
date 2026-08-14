"""Exceptions which do not map to errors at the following URL, or simple
errors given by the cloud recognition service.

https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#result-codes
"""

from beartype import beartype

from vws.response import Response  # noqa: TC001


@beartype
class RequestEntityTooLargeError(Exception):
    """Exception raised when the given image is too large."""

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response returned by Vuforia.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """The response returned by Vuforia which included this error."""
        return self._response


@beartype
class TargetProcessingTimeoutError(Exception):
    """Exception raised when waiting for a target to be processed times
    out.
    """


@beartype
class DatabaseIdNotSetError(Exception):
    """Exception raised when an operation which needs a database ID is used
    on a client which was not given one.
    """


@beartype
class RecoCountsReportNotReadyError(Exception):
    """Exception raised when a reco counts report is downloaded before
    Vuforia has generated it.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response returned by the report's download URL.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """The response returned by the download URL."""
        return self._response


@beartype
class RecoCountsReportDownloadError(Exception):
    """Exception raised when downloading a reco counts report fails.

    This is raised, for example, when the report's URL has expired.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response returned by the report's download URL.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """The response returned by the download URL."""
        return self._response


@beartype
class RecoCountsReportTimeoutError(Exception):
    """Exception raised when waiting for a reco counts report to be
    generated times out.
    """


@beartype
class ServerError(Exception):  # pragma: no cover
    """Exception raised when VWS returns a server error."""

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response returned by Vuforia.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """The response returned by Vuforia which included this error."""
        return self._response
