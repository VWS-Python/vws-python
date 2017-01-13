"""
Tests for getting a target record.

https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Record-Using-the-VWS-API
"""

import base64
import io

import pytest
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    VuforiaServerCredentials,
    add_target_to_vws,
    assert_vws_response,
)
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestGetRecord:
    """
    Tests for getting a target record.
    """

    def test_get_target(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        name = 'my_example_name'
        width = 1234

        data = {
            'name': name,
            'width': width,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        target_id = response.json()['target_id']
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
        assert


    """
    Test with active flag set to something

    Test that status eventually changes.

    GET with a slash at the end

    Test setting active flag to None.
    """
