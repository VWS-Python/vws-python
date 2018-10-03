"""
Custom exceptions for Vuforia errors.
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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response

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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response


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
        self._response = response

    @property
    def response(self) -> Response:
        """
        The response returned by Vuforia which included this error.
        """
        return self._response
