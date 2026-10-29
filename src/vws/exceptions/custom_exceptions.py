"""HTTP errors shared by the supported Vuforia APIs."""

from beartype import beartype

from vws.response import Response  # noqa: TC001


@beartype
class ServerError(Exception):
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
