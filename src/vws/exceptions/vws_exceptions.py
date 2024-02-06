"""
Exception raised when Vuforia returns a response with a result code matching
one of those documented at
https://library.vuforia.com/web-api/cloud-targets-web-services-api#result-codes.
"""

import json
from urllib.parse import urlparse

from vws.exceptions.base_exceptions import VWSException


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
        return path.split(sep="/", maxsplit=2)[-1]


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
        return path.split(sep="/", maxsplit=2)[-1]


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


class ProjectInactive(VWSException):
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectInactive'.
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
        response_body = self.response.request_body or b""
        request_json = json.loads(s=response_body)
        return str(request_json["name"])


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
        return path.split(sep="/", maxsplit=2)[-1]


class TooManyRequests(VWSException):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'TooManyRequests'.
    """
