"""
Tests for giving JSON data to endpoints which do not expect it.
"""

import json
from urllib.parse import urlparse

import pytest
import requests
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
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
        endpoint: TargetAPIEndpoint,
    ) -> None:
        """
        Giving JSON to endpoints which do not take any JSON data returns
        error responses.
        """
        if endpoint.prepared_request.headers.get(
            'Content-Type'
        ) == 'application/json':
            return
        content = bytes(json.dumps({'key': 'value'}), encoding='utf-8')
        content_type = 'application/json'
        date = rfc_1123_date()

        endpoint_headers = dict(endpoint.prepared_request.headers)

        netloc = urlparse(endpoint.prepared_request.url).netloc

        authorization_string = authorization_header(
            access_key=endpoint.access_key,
            secret_key=endpoint.secret_key,
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

        assert response.text == ''
        assert 'Content-Type' not in response.headers
        if netloc == 'cloudreco.vuforia.com':
            assert response.status_code == codes.UNSUPPORTED_MEDIA_TYPE
            # TODO response headers
        else:
            assert response.status_code == codes.BAD_REQUEST
