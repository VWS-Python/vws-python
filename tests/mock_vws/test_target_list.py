"""
Tests for the mock of the target list endpoint.
"""

import pytest
import requests
from requests import codes
from requests_mock import GET

from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestTargetList:
    """
    Tests for the mock of the database summary endpoint at `/summary`.
    """

    def test_success(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     ) -> None:
        """It is possible to get a success response."""
        date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type=endpoint.content_type or '',
            date=date,
            request_path='/targets',
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/targets',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.OK
        expected_keys = {'result_code', 'transaction_id', 'results'}
        assert response.json().keys() == expected_keys
        assert response.json()['results'] == []
