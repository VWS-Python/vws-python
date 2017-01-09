"""
Tests for getting a target record.

https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Record-Using-the-VWS-API
"""

import pytest
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import VuforiaServerCredentials, assert_vws_response
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestGetRecord:
    """
    Tests for getting a target record.
    """

    def test_get_target(self,
                        target_id: str,
                        vuforia_server_credentials: VuforiaServerCredentials,
                        ) -> None:
        """
        Details of a target are returned.
        """
        request_path = '/targets/' + target_id

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path=request_path,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        expected_keys = {
            'result_code',
            'transaction_id',
            'target_record',
            'status',
        }

        assert set(response.json().keys()) == expected_keys

        target_record = response.json()['target_record']

        expected_target_record_keys = {
            'target_id',
            'active_flag',
            'name',
            'width',
            'tracking_rating',
            'reco_rating',
        }

        assert set(target_record.keys()) == expected_target_record_keys
        assert target_id == target_record['target_id']
