"""
Exceptions which match errors raised by the Vuforia Cloud Recognition Web APIs.
"""


from beartype import beartype

from vws.exceptions.base_exceptions import CloudRecoError


@beartype
class MaxNumResultsOutOfRangeError(CloudRecoError):
    """
    Exception raised when the ``max_num_results`` given to the Cloud Recognition Web API
    query endpoint is out of range.
    """

@beartype
class InactiveProjectError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code
    'InactiveProject'.
    """

@beartype
class BadImageError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code 'BadImage'.
    """

@beartype
class AuthenticationFailureError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
    """

@beartype
class RequestTimeTooSkewedError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """
