"""
Base exceptions for errors returned by Vuforia Web Services or the Vuforia
Cloud Recognition Web API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .response import Response


class CloudRecoError(Exception):
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


class VWSError(Exception):
    """
    Base class for Vuforia Web Services errors.

    These errors are defined at
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#result-codes.
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
