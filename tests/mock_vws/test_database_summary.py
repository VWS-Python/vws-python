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

    Because there is a small delay in sending requests and Vuforia isn't
    consistent, some leeway is given.
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

    def test_old_date(self,
                      vuforia_server_credentials: VuforiaServerCredentials,
                      ) -> None:
        """
        If the date header is set to more than five minutes before the request
        is made, an error is returned.
        """
        with freeze_time(datetime.now() - timedelta(minutes=5, seconds=1)):
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

        assert response.status_code == codes.FORBIDDEN
        assert response.json().keys() == {'transaction_id', 'result_code'}
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == 'RequestTimeTooSkewed'

    def test_not_too_old_date(self,
                              vuforia_server_credentials:
                              VuforiaServerCredentials,
                              ) -> None:
        """
        If a date header is just under five minutes ago, no error is returned.
        """
        with freeze_time(datetime.now() - timedelta(minutes=4, seconds=50)):
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
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == 'Success'

    def test_date_too_late(self,
                           vuforia_server_credentials:
                           VuforiaServerCredentials,
                           )-> None:
        """
        If a date header is a little over five minutes in the future, an error
        is raised.
        """
        with freeze_time(datetime.now() + timedelta(minutes=5, seconds=3)):
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

        assert response.status_code == codes.FORBIDDEN
        assert response.json().keys() == {'transaction_id', 'result_code'}
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == 'RequestTimeTooSkewed'

    def test_not_too_late(self,
                          vuforia_server_credentials:
                          VuforiaServerCredentials,
                          )-> None:
        """
        If a date header is a little under 5 minutes in the future, no error is
        raised.
        """
        with freeze_time(datetime.now() + timedelta(minutes=4, seconds=59)):
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
        assert response.json().keys() == {'transaction_id', 'result_code'}
        assert is_valid_transaction_id(response.json()['transaction_id'])
        assert response.json()['result_code'] == 'Success'
