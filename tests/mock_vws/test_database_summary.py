"""
Tests for the mock of the database summary endpoint.
"""

import pytest
import requests
from requests import codes
from requests_mock import GET

from tests.conftest import VuforiaServerCredentials
from tests.mock_vws.utils import is_valid_transaction_id
from vws._request_utils import authorization_header, rfc_1123_date


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

        content_type = 'application/json'

        signature_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type=content_type,
            date=date,
            request_path='/summary',
        )

        headers = {
            "Authorization": signature_string,
            "Date": date,
            "Content-Type": content_type,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.OK

    def test_no_date_header(self,
                            vuforia_server_credentials: VuforiaServerCredentials,  # noqa: E501
                            ) -> None:
        """
        A `BAD_REQUEST` response is returned when no date header is given.
        """
        date = rfc_1123_date()

        content_type = 'application/json'

        signature_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type=content_type,
            date=date,
            request_path='/summary',
        )

        headers = {
            "Authorization": signature_string,
            "Content-Type": content_type,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.BAD_REQUEST
        assert response.json().keys() == {'transaction_id', 'result_code'}
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == 'Fail'
