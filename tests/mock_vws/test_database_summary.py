"""
Tests for the mock of the database summary endpoint.
"""

from datetime import datetime, timedelta

import pytest
import requests
from freezegun import freeze_time
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.conftest import VuforiaServerCredentials
from tests.mock_vws.utils import is_valid_transaction_id
from vws._request_utils import authorization_header, rfc_1123_date


def get_signature_string(date: str,
                         vuforia_server_credentials: VuforiaServerCredentials,
                         ) -> str:
    """
    Args:
        date: The `Date` header to be given in the request.
        vuforia_server_credentials: The credentials to authenticate with the
            VWS server.

    Returns:
        The signature to use as the `Authorization` header to the request.
    """
    signature_string = authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        content_type='',
        date=date,
        request_path='/summary',
    )
    return signature_string

def assert_vws_failure(response, status_code, result_code):
    assert response.status_code == status_code
    assert response.json().keys() == {'transaction_id', 'result_code'}
    assert is_valid_transaction_id(response.json()['transaction_id'])
    assert response.json()['result_code'] == result_code


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestSummary:
    """
    Tests for the mock of the database summary endpoint at `/summary`.
    """

    def test_success(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     ) -> None:
        """It is possible to get a success response from a VWS endpoint which
        requires authorization."""
        date = rfc_1123_date()

        signature_string = get_signature_string(
            date=date,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        headers = {
            "Authorization": signature_string,
            "Date": date,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.OK


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestHeaders:
    """
    XXX
    """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAuthorizationHeader:
    """
    Tests for what happens when the `Authorization` header isn't as expected.
    """

    def test_missing(self):
        """
        An `UNAUTHORIZED` response is returned when no `Authorization` header
        is given.
        """
        headers = {
            "Date": rfc_1123_date(),
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNAUTHORIZED,
            result_code=ResultCodes.AUTHENTICATION_FAILURE.value,
        )

@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDateHeader:
    """
    Tests for what happens when the `Date` header isn't as expected.
    """

    def test_no_date_header(self,
                            vuforia_server_credentials:
                            VuforiaServerCredentials,
                            ) -> None:
        """
        A `BAD_REQUEST` response is returned when no `Date` header is given.
        """
        date = rfc_1123_date()

        signature_string = get_signature_string(
            date=date,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        headers = {
            "Authorization": signature_string,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
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
                                   VuforiaServerCredentials) -> None:
        """
        A `BAD_REQUEST` response is returned when the date given in the date
        header is not in the expected format (RFC 1123).
        """
        with freeze_time(datetime.now()):
            date = rfc_1123_date()
            date_incorrect_format = datetime.now().strftime("%a %b %d %H:%M:%S %Y")

        signature_string = get_signature_string(
            date=date,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        headers = {
            "Authorization": signature_string,
            "Date": date_incorrect_format,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
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

        signature_string = get_signature_string(
            date=date,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        headers = {
            "Authorization": signature_string,
            "Date": date,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )

        assert response.status_code == expected_status
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == expected_result
