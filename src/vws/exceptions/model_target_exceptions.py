"""Exceptions raised by the Vuforia Model Target Web API.

See
https://developer.vuforia.com/library/vuforia-engine/web-api/model-target-web-api/.
"""

import json
from typing import Any

from beartype import beartype

from vws.reports import ModelTargetGenerationDetail
from vws.response import Response  # noqa: TC001


@beartype
def _is_json_object(*, value: object) -> bool:
    """Get whether a decoded JSON value is an object.

    Args:
        value: A decoded JSON value.

    Returns:
        Whether the value is a JSON object.
    """
    return isinstance(value, dict)


@beartype
def _json_object(*, value: str) -> dict[str, Any]:
    """Get a JSON object from a string.

    Args:
        value: A string which may be a JSON object.

    Returns:
        The JSON object, or an empty dictionary if the string is not a
        JSON object.
    """
    try:
        loaded: Any = json.loads(s=value)
    except json.JSONDecodeError:
        return {}

    if not _is_json_object(value=loaded):
        return {}

    json_object: dict[str, Any] = loaded
    return json_object


@beartype
def _error_dict(*, response: Response) -> dict[str, Any]:
    """Get the error object of a Model Target Web API error response.

    Args:
        response: The response returned by Vuforia.

    Returns:
        The error object, or an empty dictionary if the response has no
        error object. Some errors, such as those given by the load
        balancer in front of Vuforia, are not shaped like Model Target
        Web API errors.
    """
    body = _json_object(value=response.text)
    if "error" not in body:
        return {}

    error: Any = body["error"]
    if not _is_json_object(value=error):
        return {}

    error_dict: dict[str, Any] = error
    return error_dict


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
                code=detail["code"],
                message=detail["message"],
            )
            for detail in error["details"]
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
