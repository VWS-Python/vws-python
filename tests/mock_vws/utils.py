"""
Utilities for tests for the VWS mock.
"""

from string import hexdigits
from typing import Optional
from urllib.parse import urljoin

from requests.models import Response

from common.constants import ResultCodes


class Endpoint:
    """
    Details of endpoints to be called in tests.
    """

    def __init__(self,
                 example_path: str,
                 method: str,
                 successful_headers_result_code: ResultCodes,
                 successful_headers_status_code: int,
                 content_type: Optional[str],
                 content: bytes,
                 ) -> None:
        """
        Args:
            example_path: An example path for calling the endpoint.
            method: The HTTP method for the endpoint.
            successful_headers_result_code: The expected result code if the
                example path is requested with the method.
            successful_headers_status_code: The expected status code if the
                example path is requested with the method.
            content: The data to send with the request.

        Attributes:
            example_path: An example path for calling the endpoint.
            method: The HTTP method for the endpoint.
            content_type: The `Content-Type` header to send, or `None` if one
                should not be sent.
            content: The data to send with the request.
            url: The URL to call the path with.
            successful_headers_result_code: The expected result code if the
                example path is requested with the method.
            successful_headers_status_code: The expected status code if the
                example path is requested with the method.
        """
        self.example_path = example_path
        self.method = method
        self.content_type = content_type
        self.content = content
        self.url = urljoin('https://vws.vuforia.com/', example_path)
        self.successful_headers_status_code = successful_headers_status_code
        self.successful_headers_result_code = successful_headers_result_code


def is_valid_transaction_id(string: str) -> bool:
    """
    Return whether or not a given string could be a valid Vuforia transaction
    id.

    A valid transaction id looks something like:

        dde268b0136e4c03aedfdaf3cb465815

    Args:
        string: A string to check for whether it is a valid transaction id.

    Returns:
        Whether or not a given string could be a valid Vuforia transaction id.
    """
    if len(string) != 32:
        return False

    return all(char in hexdigits for char in string)


def assert_vws_failure(response: Response,
                       status_code: int,
                       result_code: ResultCodes) -> None:
    """
    Assert that a VWS failure response is as expected.

    https://library.vuforia.com/articles/Solution/How-To-Interperete-VWS-API-Result-Codes
    implies that the expected status code can be worked out from the result
    code. However, this is not the case as the real results differ from the
    documentation.

    For example, it is possible to get a "Fail" result code and a 400 error.

    Args:
        response: The response returned by a request to VWS.
        status_code: The expected status code of the response.
        result_code: The expected result code of the response.

    Raises:
        AssertionError: The response is not in the expected VWS error format
        for the given codes.
    """
    message = 'Expected {expected}, got {actual}.'
    assert response.status_code == status_code, message.format(
        expected=status_code,
        actual=response.status_code,
    )
    assert response.json().keys() == {'transaction_id', 'result_code'}
    assert is_valid_transaction_id(response.json()['transaction_id'])
    assert response.json()['result_code'] == result_code.value
