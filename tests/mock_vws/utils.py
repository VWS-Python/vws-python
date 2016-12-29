"""
Utilities for tests for the VWS mock.
"""

from string import hexdigits

from requests.models import Response


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
                       result_code: str) -> None:
    """
    Assert that a VWS failure response is as expected.

    Args:
        response: The response returned by a request to VWS.
        status_code: The expected status code of the response.
        result_code: The expected result code of the response.

    Raises:
        AssertionError: The response is not in the expected VWS error format
        for the given codes.
    """
    assert response.status_code == status_code
    assert response.json().keys() == {'transaction_id', 'result_code'}
    assert is_valid_transaction_id(response.json()['transaction_id'])
    assert response.json()['result_code'] == result_code
