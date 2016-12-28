"""
Tests for when endpoints are called with unexpected header data.
"""

from datetime import datetime, timedelta
from urllib.parse import urljoin

import pytest
import requests
# from constantly import ValueConstant, Values
from freezegun import freeze_time
from requests import codes
from requests.models import Response
from requests_mock import GET, POST

from common.constants import ResultCodes
from tests.conftest import VuforiaServerCredentials
from tests.mock_vws.utils import is_valid_transaction_id
from vws._request_utils import authorization_header, rfc_1123_date


class Route:
    def __init__(self, path, method):
        self.path = path
        self.method = method


# class ROUTES(Values):
#     """
#     Routes to test headers for.
#     """
#     # ADD_TARGET = ValueConstant(Route(path='/targets', method=POST))
#     DATABASE_SUMMARY = ValueConstant(Route(path='/summary', method=GET))
#     TARGET_LIST = ValueConstant(Route(path='/targets', method=GET))

@pytest.fixture(
    params=[
        Route(path='/summary', method=GET),
        Route(path='/targets', method=GET),
        Route(path='/targets', method=POST),
    ],
    ids=[
        'database_summary',
        'target_list',
        'add_target',
    ],
)
def route(request):
    return request.param


def assert_vws_failure(response: Response,
                       status_code: int,
                       result_code: str) -> None:
    """
    Assert that a VWS failure response is as expected.

    Args:
        response: The response returned by a request to VWS.
        status_code: The expected status code of the response.
        result_code: The expected result code of the response.

    Raises:
        AssertionError: The response is not in the expected VWS error format
        for the given codes.
    """
    assert response.status_code == status_code
    assert response.json().keys() == {'transaction_id', 'result_code'}
    assert is_valid_transaction_id(response.json()['transaction_id'])
    assert response.json()['result_code'] == result_code


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestHeaders:
    """
    Tests for what happens when the headers are not as expected.
    """

    def test_empty(self, route) -> None:
        """
        When no headers are given, an `UNAUTHORIZED` response is returned.
        """
        response = requests.request(
            method=route.method,
            url=urljoin('https://vws.vuforia.com/', route.path),
            headers={},
            data=b'',
        )
        assert_vws_failure(
            response=response,
            status_code=codes.UNAUTHORIZED,
            result_code=ResultCodes.AUTHENTICATION_FAILURE.value,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAuthorizationHeader:
    """
    Tests for what happens when the `Authorization` header isn't as expected.
    """

    def test_missing(self, route) -> None:
        """
        An `UNAUTHORIZED` response is returned when no `Authorization` header
        is given.
        """
        headers = {
            "Date": rfc_1123_date(),
        }

        response = requests.request(
            method=route.method,
            url=urljoin('https://vws.vuforia.com/', route.path),
            headers=headers,
            data=b'',
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNAUTHORIZED,
            result_code=ResultCodes.AUTHENTICATION_FAILURE.value,
        )

    def test_incorrect(self, route) -> None:
        """
        If an incorrect `Authorization` header is given, a `BAD_REQUEST`
        response is given.
        """
        date = rfc_1123_date()
        signature_string = 'gibberish'

        headers = {
            "Authorization": signature_string,
            "Date": date,
        }

        response = requests.request(
            method=route.method,
            url=urljoin('https://vws.vuforia.com/', route.path),
            headers=headers,
            data=b'',
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL.value,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDateHeader:
    """
    Tests for what happens when the `Date` header isn't as expected.
    """

    def test_no_date_header(self,
                            vuforia_server_credentials:
                            VuforiaServerCredentials,
                            route,
                            ) -> None:
        """
        A `BAD_REQUEST` response is returned when no `Date` header is given.
        """
        signature_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=route.method,
            content=b'',
            content_type='',
            date='',
            request_path=route.path,
        )

        headers = {
            "Authorization": signature_string,
        }

        response = requests.request(
            method=route.method,
            url=urljoin('https://vws.vuforia.com', route.path),
            headers=headers,
            data=b'',
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL.value,
        )

    def test_incorrect_date_format(self,
                                   vuforia_server_credentials:
                                   VuforiaServerCredentials,
                                   route) -> None:
        """
        A `BAD_REQUEST` response is returned when the date given in the date
        header is not in the expected format (RFC 1123).
        """
        with freeze_time(datetime.now()):
            date_incorrect_format = datetime.now().strftime(
                "%a %b %d %H:%M:%S %Y")

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=route.method,
            content=b'',
            content_type='',
            date=date_incorrect_format,
            request_path=route.path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date_incorrect_format,
        }

        response = requests.request(
            method=route.method,
            url=urljoin('https://vws.vuforia.com/', route.path),
            headers=headers,
            data=b'',
        )
        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL.value,
        )

    @pytest.mark.parametrize('time_multiplier', [1, -1],
                             ids=(['After', 'Before']))
    @pytest.mark.parametrize(
        ['time_difference_from_now', 'expected_status', 'expected_result'],
        [
            (
                timedelta(minutes=4, seconds=50),
                codes.OK,
                ResultCodes.SUCCESS.value,
            ),
            (
                timedelta(minutes=5, seconds=10),
                codes.FORBIDDEN,
                ResultCodes.REQUEST_TIME_TOO_SKEWED.value,
            ),
        ],
        ids=(['Within Range', 'Out of Range']),
    )
    def test_date_skewed(self,
                         vuforia_server_credentials: VuforiaServerCredentials,
                         time_difference_from_now: timedelta,
                         expected_status: str,
                         expected_result: str,
                         time_multiplier: int,
                         route,
                         ) -> None:
        """
        If a date header is within five minutes before or after the request
        is sent, no error is returned.

        If the date header is more than five minutes before or after the
        request is sent, a `FORBIDDEN` response is returned.

        Because there is a small delay in sending requests and Vuforia isn't
        consistent, some leeway is given.
        """
        time_difference_from_now *= time_multiplier
        with freeze_time(datetime.now() + time_difference_from_now):
            date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=route.method,
            content=b'',
            content_type='',
            date=date,
            request_path=route.path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }

        response = requests.request(
            method=route.method,
            url=urljoin('https://vws.vuforia.com/', route.path),
            headers=headers,
            data=b'',
        )

        assert response.status_code == expected_status
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == expected_result
