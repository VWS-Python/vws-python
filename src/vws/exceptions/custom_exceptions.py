import requests


class UnknownVWSErrorPossiblyBadName(Exception):
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


class TargetProcessingTimeout(Exception):
    """
    Exception raised when waiting for a target to be processed times out.
    """
