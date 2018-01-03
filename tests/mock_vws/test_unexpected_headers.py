"""
Tests for when endpoints are called with unexpected header data.
"""

from datetime import datetime, timedelta

import pytest
import requests
from freezegun import freeze_time
from requests import codes
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
    VuforiaDatabaseKeys,
    assert_vws_failure,
    assert_vws_response,
    authorization_header,
    rfc_1123_date,
)

from mock_vws._constants import ResultCodes


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestHeaders:
    """
    Tests for what happens when the headers are not as expected.
    """

    def test_empty(self, endpoint: TargetAPIEndpoint) -> None:
        """
        When no headers are given, an `UNAUTHORIZED` response is returned.
        """
        endpoint.prepared_request.prepare_headers(headers={})
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
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
        date = rfc_1123_date()

        headers = {
            'Date': date,
        }

        endpoint.prepared_request.prepare_headers(headers=headers)
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
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

        headers = {
            'Authorization': 'gibberish',
            'Date': date,
        }

        endpoint.prepared_request.prepare_headers(headers=headers)
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
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
        authorization_string = authorization_header(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=endpoint.prepared_request.method,
            content=endpoint.prepared_request.body,
            content_type=endpoint.prepared_request.headers['Content-Type'],
            date='',
            request_path=endpoint.prepared_request.path_url,
        )

        headers = {
            'Authorization': authorization_string,
        }

        endpoint.prepared_request.prepare_headers(headers=headers)
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
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
            method=endpoint.prepared_request.method,
            content=endpoint.prepared_request.body,
            content_type=endpoint.prepared_request.headers['Content-Type'],
            date=date_incorrect_format,
            request_path=endpoint.prepared_request.path_url,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date_incorrect_format,
        }

        endpoint.prepared_request.prepare_headers(headers=headers)
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    @pytest.mark.parametrize(
        'time_multiplier',
        [1, -1],
        ids=(['After', 'Before']),
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
            method=endpoint.prepared_request.method,
            content=endpoint.prepared_request.body,
            content_type=endpoint.prepared_request.headers['Content-Type'],
            date=date,
            request_path=endpoint.prepared_request.path_url,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
        }

        endpoint.prepared_request.prepare_headers(headers=headers)
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
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
            method=endpoint.prepared_request.method,
            content=endpoint.prepared_request.body,
            content_type=endpoint.prepared_request.headers['Content-Type'],
            date=date,
            request_path=endpoint.prepared_request.path_url,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
        }

        endpoint.prepared_request.prepare_headers(headers=headers)
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
        )

        assert_vws_response(
            response=response,
            status_code=endpoint.successful_headers_status_code,
            result_code=endpoint.successful_headers_result_code,
        )
