"""
Tests for giving JSON data to endpoints which do not expect it.
"""

import json

import pytest
import requests
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
    VuforiaDatabaseKeys,
    assert_vws_failure,
    authorization_header,
    rfc_1123_date,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUnexpectedJSON:
    """
    Tests for giving JSON to endpoints which do not expect it.
    """

    def test_does_not_take_data(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        endpoint: TargetAPIEndpoint,
    ) -> None:
        """
        Giving JSON to endpoints which do not take any JSON data returns
        error responses.
        """
        if endpoint.prepared_request.headers.get('Content-Type'):
            return
        content = bytes(json.dumps({'key': 'value'}), encoding='utf-8')
        content_type = 'application/json'
        date = rfc_1123_date()

        endpoint_headers = dict(endpoint.prepared_request.headers)
        assert isinstance(content_type, str)

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=str(endpoint.prepared_request.method),
            content=content,
            content_type=content_type,
            date=date,
            request_path=endpoint.prepared_request.path_url,
        )

        headers = {
            **endpoint_headers,
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': content_type,
        }

        endpoint.prepared_request.prepare_body(  # type: ignore
            data=content,
            files=None,
        )
        endpoint.prepared_request.prepare_headers(  # type: ignore
            headers=headers,
        )
        endpoint.prepared_request.prepare_content_length(  # type: ignore
            body=content,
        )
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
        )

        # This is an undocumented difference between `/summary` and other
        # endpoints.
        if endpoint.prepared_request.path_url == '/summary':
            assert_vws_failure(
                response=response,
                status_code=codes.UNAUTHORIZED,
                result_code=ResultCodes.AUTHENTICATION_FAILURE,
            )
            return

        assert response.status_code == codes.BAD_REQUEST
        assert response.text == ''
        assert 'Content-Type' not in response.headers
