"""
Tests for giving JSON data to endpoints which do not expect it.
"""

import json

import pytest
import requests
from requests import codes

from common.constants import ResultCodes
from tests.mock_vws.utils import Endpoint, assert_vws_failure
from tests.utils import VuforiaDatabaseKeys
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUnexpectedJSON:
    """
    Tests for giving JSON to endpoints which do not expect it.
    """

    def test_does_not_take_data(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        endpoint_no_data: Endpoint,
    ) -> None:
        """
        Giving JSON to endpoints which do not take any JSON data returns
        error responses.
        """
        endpoint = endpoint_no_data
        content = bytes(json.dumps({'key': 'value'}), encoding='utf-8')
        date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.access_key,
            secret_key=vuforia_database_keys.secret_key,
            method=endpoint.method,
            content=content,
            content_type='application/json',
            date=date,
            request_path=endpoint.example_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': 'application/json',
        }

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=content,
        )

        # This is an undocumented difference between `/summary` and other
        # endpoints.
        if endpoint.example_path == '/summary':
            assert_vws_failure(
                response=response,
                status_code=codes.UNAUTHORIZED,
                result_code=ResultCodes.AUTHENTICATION_FAILURE,
            )
        else:
            assert response.status_code == codes.BAD_REQUEST
            assert response.text == ''
            assert 'Content-Type' not in response.headers
