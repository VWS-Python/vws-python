"""
XXX
"""

import pytest
import requests
from requests import codes
from requests_mock import GET
from urllib.parse import urljoin

from tests.conftest import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


endpoints = ['/summary']


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestInvalidGivenId:
    """
    XXX
    """

    @pytest.mark.parametrize('endpoint', endpoints)
    def test_not_done(self, endpoint, vuforia_server_credentials: VuforiaServerCredentials) -> None:
        date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type='',
            date=date,
            request_path=endpoint,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }

        response = requests.request(
            method=GET,
            url=urljoin('https://vws.vuforia.com/', endpoint, '/gibberish_id'),
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.OK
