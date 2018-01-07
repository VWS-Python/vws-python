"""
Tests for giving invalid JSON to endpoints.
"""

from datetime import datetime, timedelta

import pytest
import requests
from freezegun import freeze_time
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
    VuforiaDatabaseKeys,
    assert_vws_failure,
    authorization_header,
    rfc_1123_date,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestInvalidJSON:
    """
    Tests for giving invalid JSON to endpoints.
    """

    def test_does_not_take_data(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        endpoint: TargetAPIEndpoint,
    ) -> None:
        """
        Giving invalid JSON to endpoints returns error responses.
        """
        content = b'a'
        date = rfc_1123_date()

        endpoint_headers = dict(endpoint.prepared_request.headers)
        content_type = endpoint_headers.get('Content-Type', '')
        assert isinstance(content_type, str)
        endpoint_headers = dict(endpoint.prepared_request.headers)

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
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
        }

        endpoint.prepared_request.prepare_body(  # type: ignore
            data=content,
            files=None,
        )

        endpoint.prepared_request.prepare_headers(  # type: ignore
            headers=headers,
        )
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
        )

        if content_type:
            assert_vws_failure(
                response=response,
                status_code=codes.BAD_REQUEST,
                result_code=ResultCodes.FAIL,
            )
            return

        # This is an undocumented difference between `/summary` and other
        # endpoints.
        if endpoint.prepared_request.path_url == '/summary':
            assert_vws_failure(
                response=response,
                status_code=codes.UNAUTHORIZED,
                result_code=ResultCodes.AUTHENTICATION_FAILURE,
            )
            return

        assert response.status_code == codes.BAD_REQUEST
        assert response.text == ''
        assert 'Content-Type' not in response.headers

    # def test_does_not_take_data_skewed_time(  # pylint: disable=invalid-name
    #     self,
    #     vuforia_database_keys:
    #     VuforiaDatabaseKeys,
    #     endpoint_no_data: TargetAPIEndpoint,
    # ) -> None:
    #     """
    #     Of the endpoints which do not take data, only `/summary` gives a
    #     `REQUEST_TIME_TOO_SKEWED` error if invalid JSON is given at with a
    #     skewed date.
    #     """
    #     endpoint = endpoint_no_data
    #     content = b'a'
    #     assert not endpoint.content_type
    #
    #     with freeze_time(datetime.now() + timedelta(minutes=10)):
    #         date = rfc_1123_date()
    #
    #     authorization_string = authorization_header(
    #         access_key=vuforia_database_keys.server_access_key,
    #         secret_key=vuforia_database_keys.server_secret_key,
    #         method=endpoint.method,
    #         content=content,
    #         content_type='',
    #         date=date,
    #         request_path=endpoint.example_path,
    #     )
    #
    #     headers = {
    #         'Authorization': authorization_string,
    #         'Date': date,
    #     }
    #
    #     response = requests.request(
    #         method=endpoint.method,
    #         url=endpoint.url,
    #         headers=headers,
    #         data=content,
    #     )
    #
    #     # This is an undocumented difference between `/summary` and other
    #     # endpoints.
    #     if endpoint.example_path == '/summary':
    #         assert_vws_failure(
    #             response=response,
    #             status_code=codes.FORBIDDEN,
    #             result_code=ResultCodes.REQUEST_TIME_TOO_SKEWED,
    #         )
    #         return
    #
    #     assert response.status_code == codes.BAD_REQUEST
    #     assert response.text == ''
    #     assert 'Content-Type' not in response.headers
    #
