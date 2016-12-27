"""
Tests for the mock of the database summary endpoint.
"""

import pytest
import requests
from requests import codes
from requests.models import Response
from requests_mock import GET

from tests.conftest import VuforiaServerCredentials
from tests.mock_vws.utils import is_valid_transaction_id
from vws._request_utils import authorization_header, rfc_1123_date


def get_signature_string(date: str,
                         vuforia_server_credentials: VuforiaServerCredentials,
                         ) -> bytes:
    """
    Return a string to be used in the `Authorization` header to for a request
    to the database summary endpoint.

    Args:
        date: The `Date` header to be encoded in the `Authorization` header.
        vuforia_server_credentials: The credentials to authenticate with the
            VWS server.

    Returns:
        The signature to use as the `Authorization` header to the request.
    """
    return authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        content_type='',
        date=date,
        request_path='/summary',
    )


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


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestSummary:
    """
    Tests for the mock of the database summary endpoint at `/summary`.
    """

    def test_success(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     ) -> None:
        """It is possible to get a success response from a VWS endpoint which
        requires authorization."""
        date = rfc_1123_date()

        signature_string = get_signature_string(
            date=date,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        headers = {
            "Authorization": signature_string,
            "Date": date,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.OK
