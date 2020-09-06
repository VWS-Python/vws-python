"""
Custom exceptions for Vuforia errors.
"""

import json
from urllib.parse import urlparse

import requests
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
    Base class for Vuforia Web Service errors.
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


class UnknownVWSErrorPossiblyBadName(VWSException):
    """
    Exception raised when VWS returns an HTML page which says "Oops, an error
    occurred".

    This has been seen to happen when the given name includes a bad character.
    """


class ConnectionErrorPossiblyImageTooLarge(requests.ConnectionError):
    """
    Exception raised when a ConnectionError is raised from a query. This has
    been seen to happen when the given image is too large.
    """


class MatchProcessing(CloudRecoException):
    """
    Exception raised when a query is made with an image which matches a target
    which is processing or has recently been deleted.
    """


class MaxNumResultsOutOfRange(CloudRecoException):
    """
    Exception raised when the ``max_num_results`` given to the Cloud
    Recognition Web API query endpoint is out of range.
    """


class UnknownTarget(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'UnknownTarget'.
    """

    @property
    def target_id(self) -> str:
        """
        The unknown target ID.
        """
        path = urlparse(self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep='/', maxsplit=2)[-1]


class Fail(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'Fail'.
    """


class BadImage(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'BadImage'.
    """


class AuthenticationFailure(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
    """


# See https://github.com/VWS-Python/vws-python/issues/822.
class RequestQuotaReached(VWSException):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestQuotaReached'.
    """


class TargetStatusProcessing(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusProcessing'.
    """

    @property
    def target_id(self) -> str:
        """
        The processing target ID.
        """
        path = urlparse(self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep='/', maxsplit=2)[-1]


class ProjectInactive(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectInactive' or 'InactiveProject'.
    """


class MetadataTooLarge(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'MetadataTooLarge'.
    """


class RequestTimeTooSkewed(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """


class TargetNameExist(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetNameExist'.
    """

    @property
    def target_name(self) -> str:
        """
        The target name which already exists.
        """
        response_body = self.response.request.body or b''
        request_json = json.loads(response_body)
        return str(request_json['name'])


class ImageTooLarge(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'ImageTooLarge'.
    """


class TargetStatusNotSuccess(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusNotSuccess'.
    """

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
class DateRangeError(VWSException):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'DateRangeError'.
    """


# This is not simulated by the mock.
class TargetQuotaReached(VWSException):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetQuotaReached'.
    """


# This is not simulated by the mock.
class ProjectSuspended(VWSException):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectSuspended'.
    """


# This is not simulated by the mock.
class ProjectHasNoAPIAccess(VWSException):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectHasNoAPIAccess'.
    """


class TargetProcessingTimeout(Exception):
    """
    Exception raised when waiting for a target to be processed times out.
    """
