"""
Exceptions which match errors raised by the Vuforia Cloud Recognition Web APIs.
"""

from vws.exceptions.base_exceptions import CloudRecoError


class MaxNumResultsOutOfRangeError(CloudRecoError):
    """
    Exception raised when the ``max_num_results`` given to the Cloud
    Recognition Web API query endpoint is out of range.
    """


class InactiveProjectError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code
    'InactiveProject'.
    """


class BadImageError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code
    'BadImage'.
    """


class AuthenticationFailureError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
    """


class RequestTimeTooSkewedError(CloudRecoError):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """
