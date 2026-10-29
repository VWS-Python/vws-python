"""
Exception raised when Vuforia returns a response with a result code
matching
one of those documented at
https://developer.vuforia.com/library/web-api/cloud-targets-web-services-
api#result-codes.
"""

from urllib.parse import urlparse

from beartype import beartype

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
class RequestTimeTooSkewedError(VWSError):
    """Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
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
        "BadRequest": BadRequestError,
        "Fail": FailError,
        "InvalidAcceptHeader": InvalidAcceptHeaderError,
        "InvalidInstanceId": InvalidInstanceIdError,
        "InvalidTargetType": InvalidTargetTypeError,
        "LicenseCheckFailed": LicenseCheckFailedError,
        "ProjectHasNoApiAccess": ProjectHasNoAPIAccessError,
        "ProjectInactive": ProjectInactiveError,
        "ProjectSuspended": ProjectSuspendedError,
        "QuotaExceeded": QuotaExceededError,
        "RequestQuotaReached": RequestQuotaReachedError,
        "RequestTimeTooSkewed": RequestTimeTooSkewedError,
        "TargetStatusNotSuccess": TargetStatusNotSuccessError,
        "UnknownTarget": UnknownTargetError,
    },
)
