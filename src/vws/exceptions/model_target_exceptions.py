"""Exceptions raised by the Vuforia Model Target Web API.

See
https://developer.vuforia.com/library/vuforia-engine/web-api/model-target-web-api/.
"""

import json

from beartype import beartype

from vws._json_utils import (
    JSONValue,
    json_object,
    object_field,
    object_list_field,
    string_field,
)
from vws.reports import ModelTargetGenerationDetail
from vws.response import Response


@beartype
def _json_object(*, value: str) -> dict[str, JSONValue]:
    """Return a decoded JSON object, or an empty object for invalid
    input.
    """
    try:
        return json_object(value=value)
    except json.JSONDecodeError, TypeError:
        return {}


@beartype
def _error_dict(*, response: Response) -> dict[str, JSONValue]:
    """Get the error object of a Model Target Web API error response.

    Args:
        response: The response returned by Vuforia.

    Returns:
        The error object, or an empty dictionary if the response has no
        error object. Some errors, such as those given by the load
        balancer in front of Vuforia, are not shaped like Model Target
        Web API errors.
    """
    try:
        body = _json_object(value=response.text)
        return object_field(value=body, name="error")
    except KeyError, TypeError:
        return {}


@beartype
class ModelTargetError(Exception):
    """Base class for Vuforia Model Target Web API exceptions."""

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

    @property
    def code(self) -> str:
        """The error code given by Vuforia, or an empty string."""
        error = _error_dict(response=self._response)
        return str(object=error["code"]) if "code" in error else ""

    @property
    def message(self) -> str:
        """The error message given by Vuforia, or an empty string."""
        error = _error_dict(response=self._response)
        return str(object=error["message"]) if "message" in error else ""

    @property
    def target(self) -> str:
        """The error target given by Vuforia, or an empty string."""
        error = _error_dict(response=self._response)
        return str(object=error["target"]) if "target" in error else ""

    @property
    def details(self) -> list[ModelTargetGenerationDetail]:
        """The error details given by Vuforia.

        Vuforia gives one detail per validation problem it found with a
        dataset creation request.
        """
        error = _error_dict(response=self._response)
        if "details" not in error:
            return []

        return [
            ModelTargetGenerationDetail(
                code=string_field(value=detail_object, name="code"),
                message=string_field(value=detail_object, name="message"),
            )
            for detail_object in object_list_field(value=error, name="details")
        ]


@beartype
class ModelTargetAuthenticationError(ModelTargetError):
    """Exception raised when a Model Target Web API request is not
    authenticated.

    For example, the bearer token may be missing, malformed or expired.
    """


@beartype
class ModelTargetValidationError(ModelTargetError):
    """Exception raised when Vuforia rejects a Model Target dataset
    creation
    request.

    See :attr:`~.ModelTargetError.details` for the problems which Vuforia
    found.
    """


@beartype
class UnknownModelTargetDatasetError(ModelTargetError):
    """Exception raised when no Model Target dataset matches a given UUID.

    Standard and advanced datasets are separate resources, so this is also
    raised when the given UUID matches a dataset of the other type.
    """


@beartype
class ModelTargetDatasetNotDoneError(ModelTargetError):
    """Exception raised when a Model Target dataset is downloaded before
    Vuforia has generated it.
    """


@beartype
class ModelTargetOAuth2Error(Exception):
    """Exception raised when Vuforia does not give an access token.

    For example, the given client ID and client secret may not match a set
    of Model Target Web API credentials.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia's token
                endpoint.
        """
        super().__init__(response.text)
        self._response = response

    @property
    def response(self) -> Response:
        """The response returned by Vuforia which included this error."""
        return self._response

    @property
    def error(self) -> str:
        """The OAuth2 error code, or an empty string."""
        body = _json_object(value=self._response.text)
        return str(object=body["error"]) if "error" in body else ""

    @property
    def error_description(self) -> str:
        """The OAuth2 error description, or an empty string."""
        body = _json_object(value=self._response.text)
        if "error_description" not in body:
            return ""

        return str(object=body["error_description"])


@beartype
class ModelTargetDatasetTimeoutError(Exception):
    """Exception raised when waiting for a Model Target dataset to be
    generated times out.
    """
