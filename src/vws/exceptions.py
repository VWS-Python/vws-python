"""
Custom exceptions for Vuforia errors.
"""

import json
from urllib.parse import urlparse

import requests
from requests import Response


class UnknownVWSErrorPossiblyBadName(Exception):
    """
    Exception raised when VWS returns an HTML page which says "Oops, an error
    occurred".

    This has been seen to happen when the given name includes a bad character.
    """


class ConnectionErrorPossiblyImageTooLarge(
    requests.exceptions.ConnectionError,
):
    """
    Exception raised when a ConnectionError is raised from a query. This has
    been seen to happen when the given image is too large.
    """


class MatchProcessing(Exception):
    """
    Exception raised when a query is made with an image which matches a target
    which is processing or has recently been deleted.
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


class MaxNumResultsOutOfRange(Exception):
    """
    Exception raised when the ``max_num_results`` given to the Cloud
    Recognition Web API query endpoint is out of range.
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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response

    @property
    def target_id(self) -> str:
        """
        The unknown target ID.
        """
        path = urlparse(self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep='/', maxsplit=2)[-1]


class Fail(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'Fail'.
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


class BadImage(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'BadImage'.
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


class AuthenticationFailure(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
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


# See https://github.com/adamtheturtle/vws-python/issues/822.
class RequestQuotaReached(Exception):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestQuotaReached'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class TargetStatusProcessing(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusProcessing'.
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

    @property
    def target_id(self) -> str:
        """
        The processing target ID.
        """
        path = urlparse(self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep='/', maxsplit=2)[-1]


class ProjectInactive(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectInactive' or 'InactiveProject'.
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


class MetadataTooLarge(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'MetadataTooLarge'.
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


class RequestTimeTooSkewed(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class TargetNameExist(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetNameExist'.
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

    @property
    def target_name(self) -> str:
        """
        The target name which already exists.
        """
        response_body = self.response.request.body or b''
        request_json = json.loads(response_body)
        return str(request_json['name'])


class ImageTooLarge(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'ImageTooLarge'.
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


class TargetStatusNotSuccess(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusNotSuccess'.
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

    @property
    def target_id(self) -> str:
        """
        The unknown target ID.
        """
        path = urlparse(self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep='/', maxsplit=2)[-1]


# This is not simulated by the mock.
class DateRangeError(Exception):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'DateRangeError'.
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


# This is not simulated by the mock.
class TargetQuotaReached(Exception):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetQuotaReached'.
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


# This is not simulated by the mock.
class ProjectSuspended(Exception):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectSuspended'.
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


# This is not simulated by the mock.
class ProjectHasNoAPIAccess(Exception):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectHasNoAPIAccess'.
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


class TargetProcessingTimeout(Exception):
    """
    Exception raised when waiting for a target to be processed times out.
    """
