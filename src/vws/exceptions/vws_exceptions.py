"""
Exception raised when Vuforia returns a response with a result code
matching
one of those documented at
https://developer.vuforia.com/library/web-api/cloud-targets-web-services-
api#result-codes.
"""

from urllib.parse import urlparse

from beartype import beartype

from vws._json_utils import json_object, string_field
from vws.exceptions.base_exceptions import VWSError


@beartype
def _target_id_from_url(*, url: str) -> str:
    """Return the target ID from a VWS response URL.

    Paths may include a custom base URL prefix. The target ID is the
    path segment after ``targets``, ``summary``, or ``duplicates``.
    """
    path = urlparse(url=url).path
    parts = [part for part in path.split(sep="/") if bool(part)]
    for marker in ("targets", "summary", "duplicates"):
        try:
            marker_index = parts.index(marker)
        except ValueError:
            continue
        return parts[marker_index + 1]
    message = f"Could not find a target ID in URL path {path!r}"
    raise ValueError(message)


@beartype
class UnknownTargetError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'UnknownTarget'.
    """

    @property
    def target_id(self) -> str:
        """The unknown target ID."""
        return _target_id_from_url(url=self.response.url)


@beartype
class FailError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'Fail'.
    """


@beartype
class BadImageError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'BadImage'.
    """


@beartype
class AuthenticationFailureError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
    """


@beartype
class RequestQuotaReachedError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'RequestQuotaReached'.
    """


@beartype
class TargetStatusProcessingError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'TargetStatusProcessing'.
    """

    @property
    def target_id(self) -> str:
        """The processing target ID."""
        return _target_id_from_url(url=self.response.url)


@beartype
class DateRangeError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'DateRangeError'.
    """


@beartype
class TargetQuotaReachedError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'TargetQuotaReached'.
    """


@beartype
class ProjectSuspendedError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'ProjectSuspended'.
    """


@beartype
class ProjectHasNoAPIAccessError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'ProjectHasNoApiAccess'.
    """


@beartype
class ProjectInactiveError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'ProjectInactive'.
    """


@beartype
class MetadataTooLargeError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'MetadataTooLarge'.
    """


@beartype
class RequestTimeTooSkewedError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """


@beartype
class TargetNameExistError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'TargetNameExist'.
    """

    @property
    def target_name(self) -> str:
        """The target name which already exists."""
        response_body = self.response.request_body
        if not isinstance(response_body, str | bytes):
            msg = "A target-name error response must have a request body."
            raise TypeError(msg)
        request_json = json_object(value=response_body)
        return string_field(value=request_json, name="name")


@beartype
class ImageTooLargeError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'ImageTooLarge'.
    """


@beartype
class TargetStatusNotSuccessError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'TargetStatusNotSuccess'.
    """

    @property
    def target_id(self) -> str:
        """The unknown target ID."""
        return _target_id_from_url(url=self.response.url)


@beartype
class TooManyRequestsError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'TooManyRequests'.
    """


@beartype
class InvalidAcceptHeaderError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    ``InvalidAcceptHeader``.
    """


@beartype
class InvalidInstanceIdError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    ``InvalidInstanceId``.
    """


@beartype
class BadRequestError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    ``BadRequest``.
    """


@beartype
class InvalidTargetTypeError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    ``InvalidTargetType``.
    """


@beartype
class QuotaExceededError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    ``QuotaExceeded``.
    """


@beartype
class LicenseCheckFailedError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    ``LicenseCheckFailed``.
    """


@beartype
class AuthorizationFailedError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    ``AuthorizationFailed``.
    """


VWSError.register_exceptions_by_result_code(
    exceptions_by_result_code={
        "AuthenticationFailure": AuthenticationFailureError,
        "AuthorizationFailed": AuthorizationFailedError,
        "BadImage": BadImageError,
        "BadRequest": BadRequestError,
        "DateRangeError": DateRangeError,
        "Fail": FailError,
        "ImageTooLarge": ImageTooLargeError,
        "InvalidAcceptHeader": InvalidAcceptHeaderError,
        "InvalidInstanceId": InvalidInstanceIdError,
        "InvalidTargetType": InvalidTargetTypeError,
        "LicenseCheckFailed": LicenseCheckFailedError,
        "MetadataTooLarge": MetadataTooLargeError,
        "ProjectHasNoApiAccess": ProjectHasNoAPIAccessError,
        "ProjectInactive": ProjectInactiveError,
        "ProjectSuspended": ProjectSuspendedError,
        "QuotaExceeded": QuotaExceededError,
        "RequestQuotaReached": RequestQuotaReachedError,
        "RequestTimeTooSkewed": RequestTimeTooSkewedError,
        "TargetNameExist": TargetNameExistError,
        "TargetQuotaReached": TargetQuotaReachedError,
        "TargetStatusNotSuccess": TargetStatusNotSuccessError,
        "TargetStatusProcessing": TargetStatusProcessingError,
        "UnknownTarget": UnknownTargetError,
    },
)
