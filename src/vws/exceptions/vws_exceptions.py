"""
Exception raised when Vuforia returns a response with a result code matching
one of those documented at
https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#result-codes.
"""

import json
from urllib.parse import urlparse

from beartype import beartype

from vws.exceptions.base_exceptions import VWSError


@beartype
class UnknownTargetError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'UnknownTarget'.
    """

    @property
    def target_id(self) -> str:
        """
        The unknown target ID.
        """
        path = urlparse(url=self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep="/", maxsplit=2)[-1]


@beartype
class FailError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code 'Fail'.
    """


@beartype
class BadImageError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'BadImage'.
    """


@beartype
class AuthenticationFailureError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
    """


# See https://github.com/VWS-Python/vws-python/issues/822.
@beartype
class RequestQuotaReachedError(VWSError):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestQuotaReached'.
    """


@beartype
class TargetStatusProcessingError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusProcessing'.
    """

    @property
    def target_id(self) -> str:
        """
        The processing target ID.
        """
        path = urlparse(url=self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep="/", maxsplit=2)[-1]


# This is not simulated by the mock.
@beartype
class DateRangeError(VWSError):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'DateRangeError'.
    """


# This is not simulated by the mock.
@beartype
class TargetQuotaReachedError(VWSError):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetQuotaReached'.
    """


# This is not simulated by the mock.
@beartype
class ProjectSuspendedError(VWSError):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectSuspended'.
    """


# This is not simulated by the mock.
@beartype
class ProjectHasNoAPIAccessError(VWSError):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectHasNoAPIAccess'.
    """


@beartype
class ProjectInactiveError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectInactive'.
    """


@beartype
class MetadataTooLargeError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'MetadataTooLarge'.
    """


@beartype
class RequestTimeTooSkewedError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """


@beartype
class TargetNameExistError(VWSError):
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
        return str(object=request_json["name"])


@beartype
class ImageTooLargeError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'ImageTooLarge'.
    """


@beartype
class TargetStatusNotSuccessError(VWSError):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusNotSuccess'.
    """

    @property
    def target_id(self) -> str:
        """
        The unknown target ID.
        """
        path = urlparse(url=self.response.url).path
        # Every HTTP path which can raise this error is in the format
        # `/something/{target_id}`.
        return path.split(sep="/", maxsplit=2)[-1]


@beartype
class TooManyRequestsError(VWSError):  # pragma: no cover
    """
    Exception raised when Vuforia returns a response with a result code
    'TooManyRequests'.
    """
