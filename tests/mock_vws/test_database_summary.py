"""
Tests for the mock of the database summary endpoint.
"""

from datetime import datetime, timedelta

import pytest
import requests
from freezegun import freeze_time
from requests import codes
from requests_mock import GET

from tests.conftest import VuforiaServerCredentials
from tests.mock_vws.utils import is_valid_transaction_id
from vws._request_utils import authorization_header, rfc_1123_date

from common.constants import ResultCodes


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

        content_type = 'application/json'

        signature_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type=content_type,
            date=date,
            request_path='/summary',
        )

        headers = {
            "Authorization": signature_string,
            "Date": date,
            "Content-Type": content_type,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.OK


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDateHeader:
    """
    Tests for what happens when the date header isn't as expected.
    """

    def test_no_date_header(self,
                            vuforia_server_credentials:
                            VuforiaServerCredentials,
                            ) -> None:
        """
        A `BAD_REQUEST` response is returned when no date header is given.
        """
        date = rfc_1123_date()

        content_type = 'application/json'

        signature_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type=content_type,
            date=date,
            request_path='/summary',
        )

        headers = {
            "Authorization": signature_string,
            "Content-Type": content_type,
        }

        response = requests.request(
            method=GET,
            url='https://vws.vuforia.com/summary',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.BAD_REQUEST
        assert response.json().keys() == {'transaction_id', 'result_code'}
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == 'Fail'

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

        content_type = 'application/json'

        signature_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            content_type=content_type,
            date=date,
            request_path='/summary',
        )

        headers = {
            "Authorization": signature_string,
            "Date": date,
            "Content-Type": content_type,
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
