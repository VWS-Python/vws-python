"""
"""

import pytest
import requests
from requests import codes

from common.constants import ResultCodes
from tests.mock_vws.utils import Endpoint, assert_vws_failure
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestInvalidJSON:
    """
    XXX
    """

    # TODO Skewed time AND bad json data
    def test_does_not_take_data(self,
                                vuforia_server_credentials:
                                VuforiaServerCredentials,
                                endpoint_which_does_not_take_data: Endpoint,
                                ) -> None:
        """
        XXX
        """
        endpoint = endpoint_which_does_not_take_data
        content = b'a'
        date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=endpoint.method,
            content=content,
            content_type=endpoint.content_type or '',
            date=date,
            request_path=endpoint.example_path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=content,
        )

        # This is an undocumented difference between `/summary` and other
        # endpoints.
        if endpoint.example_path == '/summary':
            assert_vws_failure(
                response=response,
                status_code=codes.UNAUTHORIZED,
                result_code=ResultCodes.AUTHENTICATION_FAILURE,
            )

        else:
            assert response.status_code == codes.BAD_REQUEST
            assert response.text == ''
            assert 'Content-Type' not in response.headers

    def test_does_not_take_data_2(self,
                                  vuforia_server_credentials:
                                  VuforiaServerCredentials,
                                  endpoint_which_does_not_take_data: Endpoint,
                                  ) -> None:
        """
        XXX
        """
        endpoint = endpoint_which_does_not_take_data
        content = b'a'
        from freezegun import freeze_time
        from datetime import datetime, timedelta

        with freeze_time(datetime.now() + timedelta(minutes=10)):
            date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=endpoint.method,
            content=content,
            content_type=endpoint.content_type or '',
            date=date,
            request_path=endpoint.example_path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=content,
        )

        # This is an undocumented difference between `/summary` and other
        # endpoints.
        if endpoint.example_path == '/summary':
            assert_vws_failure(
                response=response,
                status_code=codes.FORBIDDEN,
                result_code=ResultCodes.REQUEST_TIME_TOO_SKEWED,
            )
        else:
            assert response.status_code == codes.BAD_REQUEST
            assert response.text == ''
            assert 'Content-Type' not in response.headers

    def test_takes_data(self,
                        vuforia_server_credentials:
                        VuforiaServerCredentials,
                        endpoint_which_takes_data: Endpoint,
                        ) -> None:
        """
        XXX
        """
        endpoint = endpoint_which_takes_data
        content = b'a'
        date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=endpoint.method,
            content=content,
            content_type=endpoint.content_type or '',
            date=date,
            request_path=endpoint.example_path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=content,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )
