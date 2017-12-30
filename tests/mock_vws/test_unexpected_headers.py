"""
Tests for when endpoints are called with unexpected header data.
"""

from datetime import datetime, timedelta
from typing import Dict, Union

import pytest
import requests
from freezegun import freeze_time
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
    VuforiaDatabaseKeys,
    assert_vws_failure,
    assert_vws_response,
    authorization_header,
    rfc_1123_date,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestHeaders:
    """
    Tests for what happens when the headers are not as expected.
    """

    def test_empty(self, endpoint: TargetAPIEndpoint) -> None:
        """
        When no headers are given, an `UNAUTHORIZED` response is returned.
        """
        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers={},
            data=endpoint.content,
        )
        assert_vws_failure(
            response=response,
            status_code=codes.UNAUTHORIZED,
            result_code=ResultCodes.AUTHENTICATION_FAILURE,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAuthorizationHeader:
    """
    Tests for what happens when the `Authorization` header isn't as expected.
    """

    def test_missing(self, endpoint: TargetAPIEndpoint) -> None:
        """
        An `UNAUTHORIZED` response is returned when no `Authorization` header
        is given.
        """
        headers = {
            'Date': rfc_1123_date(),
        }

        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=endpoint.content,
        )

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
        signature_string = 'gibberish'

        headers = {
            'Authorization': signature_string,
            'Date': date,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=endpoint.content,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDateHeader:
    """
    Tests for what happens when the `Date` header isn't as expected.
    """

    def test_no_date_header(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        endpoint: TargetAPIEndpoint,
    ) -> None:
        """
        A `BAD_REQUEST` response is returned when no `Date` header is given.
        """
        signature_string = authorization_header(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=endpoint.method,
            content=endpoint.content,
            content_type=endpoint.content_type or '',
            date='',
            request_path=endpoint.example_path
        )

        headers: Dict[str, Union[bytes, str]] = {
            'Authorization': signature_string,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=endpoint.content,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_incorrect_date_format(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        endpoint: TargetAPIEndpoint,
    ) -> None:
        """
        A `BAD_REQUEST` response is returned when the date given in the date
        header is not in the expected format (RFC 1123).
        """
        with freeze_time(datetime.now()):
            date_incorrect_format = datetime.now(
            ).strftime('%a %b %d %H:%M:%S %Y')

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=endpoint.method,
            content=endpoint.content,
            content_type=endpoint.content_type or '',
            date=date_incorrect_format,
            request_path=endpoint.example_path
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date_incorrect_format,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=endpoint.content,
        )
        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    @pytest.mark.parametrize(
        'time_multiplier', [1, -1], ids=(['After', 'Before'])
    )
    def test_date_out_of_range(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        time_multiplier: int,
        endpoint: TargetAPIEndpoint,
    ) -> None:
        """
        If the date header is more than five minutes before or after the
        request is sent, a `FORBIDDEN` response is returned.

        Because there is a small delay in sending requests and Vuforia isn't
        consistent, some leeway is given.
        """
        time_difference_from_now = timedelta(minutes=5, seconds=10)
        time_difference_from_now *= time_multiplier
        with freeze_time(datetime.now() + time_difference_from_now):
            date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=endpoint.method,
            content=endpoint.content,
            content_type=endpoint.content_type or '',
            date=date,
            request_path=endpoint.example_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=endpoint.content,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.REQUEST_TIME_TOO_SKEWED,
        )

    @pytest.mark.parametrize(
        'time_multiplier', [1, -1], ids=(['After', 'Before'])
    )
    def test_date_in_range(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        time_multiplier: int,
        endpoint: TargetAPIEndpoint,
    ) -> None:
        """
        If a date header is within five minutes before or after the request
        is sent, no error is returned.

        Because there is a small delay in sending requests and Vuforia isn't
        consistent, some leeway is given.
        """
        time_difference_from_now = timedelta(minutes=4, seconds=50)
        time_difference_from_now *= time_multiplier
        with freeze_time(datetime.now() + time_difference_from_now):
            date = rfc_1123_date()
        time_difference_from_now *= time_multiplier
        with freeze_time(datetime.now() + time_difference_from_now):
            date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=endpoint.method,
            content=endpoint.content,
            content_type=endpoint.content_type or '',
            date=date,
            request_path=endpoint.example_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=endpoint.content,
        )

        assert_vws_response(
            response=response,
            status_code=endpoint.successful_headers_status_code,
            result_code=endpoint.successful_headers_result_code,
        )
