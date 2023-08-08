"""
Exceptions which do not map to errors at
https://library.vuforia.com/web-api/cloud-targets-web-services-api#result-codes
or simple errors given by the cloud recognition service.
"""


class UnknownVWSErrorPossiblyBadName(Exception):
    """
    Exception raised when VWS returns an HTML page which says "Oops, an error
    occurred".

    This has been seen to happen when the given name includes a bad character.
    """


class RequestEntityTooLarge(Exception):
    """
    Exception raised when the given image is too large.
    """


class TargetProcessingTimeout(Exception):
    """
    Exception raised when waiting for a target to be processed times out.
    """
