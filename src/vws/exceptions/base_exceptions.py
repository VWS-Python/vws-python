"""
Base exceptions for errors returned by Vuforia Web Services or the
Vuforia
Cloud Recognition Web API.
"""

from collections.abc import Mapping
from typing import ClassVar

from beartype import beartype

from vws.response import Response


@beartype
class CloudRecoError(Exception):
    """Base class for Vuforia Cloud Recognition Web API exceptions."""

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """The response returned by Vuforia which included this error."""
        return self._response


@beartype
class VWSError(Exception):
    """Base class for Vuforia Web Services errors.

    These errors are defined at
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#result-codes.
    """

    _exceptions_by_result_code: ClassVar[dict[str, type["VWSError"]]] = {}

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self._response = response

    @classmethod
    def register_exceptions_by_result_code(
        cls,
        *,
        exceptions_by_result_code: Mapping[str, type["VWSError"]],
    ) -> None:
        """Register ``result_code`` to exception mappings."""
        cls._exceptions_by_result_code.update(exceptions_by_result_code)

    @classmethod
    def from_result_code(
        cls,
        *,
        result_code: str,
        response: Response,
    ) -> "VWSError":
        """Create the mapped exception for a VWS ``result_code``."""
        exception_type = cls._exceptions_by_result_code[result_code]
        return exception_type(response=response)

    @property
    def response(self) -> Response:
        """The response returned by Vuforia which included this error."""
        return self._response
