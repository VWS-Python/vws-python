"""
Custom exceptions for Vuforia errors.

Generated with the script ``_generate_exceptions.py``.
"""

from requests import Response


class UnknownTarget(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'UnknownTarget'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class Fail(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'Fail'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class BadImage(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'BadImage'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class AuthenticationFailure(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'AuthenticationFailure'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class RequestQuotaReached(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestQuotaReached'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class TargetStatusProcessing(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusProcessing'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class ProjectInactive(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'ProjectInactive'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class MetadataTooLarge(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'MetadataTooLarge'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class RequestTimeTooSkewed(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'RequestTimeTooSkewed'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class TargetNameExist(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetNameExist'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class ImageTooLarge(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'ImageTooLarge'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class InactiveProject(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'InactiveProject'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class TargetStatusNotSuccess(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'TargetStatusNotSuccess'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response


class DateRangeError(Exception):
    """
    Exception raised when Vuforia returns a response with a result code
    'DateRangeError'.
    """

    def __init__(self, response: Response) -> None:
        """
        Args:
            response: The response to a request to Vuforia.
        """
        super().__init__()
        self.response = response
