"""
Exceptions which do not map to errors at
https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Interperete-VWS-API-Result-Codes
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


class ActiveMatchingTargetsDeleteProcessing(Exception):
    """
    Exception raised when a query is made with an image which matches a target
    which has recently been deleted.
    """
