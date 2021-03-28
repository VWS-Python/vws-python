"""
Exceptions which match errors raised by the Vuforia Cloud Recognition Web APIs.
"""


from vws.exceptions.base_exceptions import CloudRecoException


class MaxNumResultsOutOfRange(CloudRecoException):
    """
    Exception raised when the ``max_num_results`` given to the Cloud
    Recognition Web API query endpoint is out of range.
    """


class InactiveProject(CloudRecoException):
    """
    Exception raised when Vuforia returns a response with a result code
    'InactiveProject'.
    """


class BadImage(CloudRecoException):
    """
    Exception raised when Vuforia returns a response with a result code
    'BadImage'.
    """


class AuthenticationFailure(CloudRecoException):
    """
    Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
    """


class RequestTimeTooSkewed(CloudRecoException):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """
