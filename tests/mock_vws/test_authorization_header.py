"""
Tests for the `Authorization` header.
"""

from typing import Dict, Union
from urllib.parse import urlparse

import pytest
import requests
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
    assert_valid_date_header,
    assert_vws_failure,
    rfc_1123_date,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAuthorizationHeader:
    """
    Tests for what happens when the `Authorization` header is not as expected.
    """

    def test_missing(self, endpoint: TargetAPIEndpoint) -> None:
        """
        An `UNAUTHORIZED` response is returned when no `Authorization` header
        is given.
        """
        date = rfc_1123_date()
        endpoint_headers = dict(endpoint.prepared_request.headers)

        headers: Dict[str, Union[str, bytes]] = {
            **endpoint_headers,
            'Date': date,
        }

        headers.pop('Authorization', None)

        endpoint.prepared_request.prepare_headers(  # type: ignore
            headers=headers,
        )
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
        )

        netloc = urlparse(endpoint.prepared_request.url).netloc
        if netloc == 'cloudreco.vuforia.com':
            assert response.status_code == codes.UNAUTHORIZED
            assert response.text == 'Authorization header missing.'
            response_header_keys = {
                'Connection',
                'Content-Length',
                'Content-Type',
                'Date',
                'Server',
                'WWW-Authenticate',
            }

            assert response.headers.keys() == response_header_keys
            assert response.headers['Connection'] == 'keep-alive'
            expected_content_type = 'text/plain; charset=ISO-8859-1'
            assert response.headers['Content-Length'] == str(
                len(response.text)
            )
            assert response.headers['Content-Type'] == expected_content_type
            assert_valid_date_header(response=response)
            assert response.headers['Server'] == 'nginx'
            assert response.headers['WWW-Authenticate'] == 'VWS'
        else:
            assert_vws_failure(
                response=response,
                status_code=codes.UNAUTHORIZED,
                result_code=ResultCodes.AUTHENTICATION_FAILURE,
            )

    def test_incorrect(self, endpoint: TargetAPIEndpoint) -> None:
        """
        If an incorrect `Authorization` header is given, a `BAD_REQUEST`
        response is given.
        """
        date = rfc_1123_date()

        headers: Dict[str, Union[str, bytes]] = {
            **endpoint.prepared_request.headers,
            'Authorization': 'gibberish',
            'Date': date,
        }

        endpoint.prepared_request.prepare_headers(  # type: ignore
            headers=headers,
        )
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )
