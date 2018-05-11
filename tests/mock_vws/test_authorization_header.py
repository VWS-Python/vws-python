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
    assert_vwq_failure,
    rfc_1123_date,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAuthorizationHeader:
    """
    Tests for what happens when the `Authorization` header is not as expected.
    """

    def test_missing(self, any_endpoint: TargetAPIEndpoint) -> None:
        """
        An `UNAUTHORIZED` response is returned when no `Authorization` header
        is given.
        """
        endpoint = any_endpoint
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
            assert_vwq_failure(
                response=response,
                status_code=codes.UNAUTHORIZED,
                content_type='text/plain; charset=ISO-8859-1',
            )
            assert response.text == 'Authorization header missing.'
            return

        assert_vws_failure(
            response=response,
            status_code=codes.UNAUTHORIZED,
            result_code=ResultCodes.AUTHENTICATION_FAILURE,
        )

    def test_incorrect(self, any_endpoint: TargetAPIEndpoint) -> None:
        """
        If an incorrect `Authorization` header is given, a `BAD_REQUEST`
        response is given.
        """
        endpoint = any_endpoint
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

        netloc = urlparse(endpoint.prepared_request.url).netloc
        if netloc == 'cloudreco.vuforia.com':
            assert_vwq_failure(
                response=response,
                status_code=codes.UNAUTHORIZED,
                content_type='text/plain; charset=ISO-8859-1',
            )
            assert response.text == 'Malformed authorization header.'
            return

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )
