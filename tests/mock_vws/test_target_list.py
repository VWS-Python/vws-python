"""
Tests for the mock of the target list endpoint.
"""

import pytest
import requests
from requests import codes
from requests_mock import GET
from urllib.parse import urljoin

from commmon.constants import ResultCodes
from tests.utils import VuforiaServerCredentials
from tests.mock_vws.utils import assert_vws_response
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
        request_path = '/targets'

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type='',
            date=date,
            request_path=request_path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }

        response = requests.request(
            method=GET,
            url=urljoin('https://vws.vuforia.com', request_path),
            headers=headers,
            data=b'',
        )
        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )
        expected_keys = {'result_code', 'transaction_id', 'results'}
        assert response.json().keys() == expected_keys
        assert response.json()['results'] == []
