"""
Tests for getting a target record.

https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Record-Using-the-VWS-API
"""

import base64
import io
from time import sleep

import pytest
from requests import Response, codes
from requests_mock import GET

from common.constants import ResultCodes, TargetStatuses
from tests.mock_vws.utils import (
    VuforiaServerCredentials,
    add_target_to_vws,
    assert_vws_response,
)
from vws._request_utils import target_api_request


def get_target(
    target_id: str, vuforia_server_credentials: VuforiaServerCredentials
) -> Response:
    """
    Helper to make a request to the endpoint to get a target record.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        target_id: The ID of the target to return a record for.

    Returns:
        The response returned by the API.
    """
    return target_api_request(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        request_path='/targets/' + target_id,
    )


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
            'active_flag': False,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        target_id = response.json()['target_id']
        response = get_target(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials
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
        assert response.json()['status'] == TargetStatuses.PROCESSING.value
        assert target_record['active_flag'] is False
        assert target_record['name'] == name
        assert target_record['width'] == width
        assert target_record['tracking_rating'] in {-1, 0, 1, 2, 3, 4, 5}
        assert target_record['reco_rating'] == ''

    def test_active_flag_not_set(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        The active flag defaults to True if it is not set.
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
        response = get_target(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials
        )

        target_record = response.json()['target_record']
        assert target_record['active_flag'] is True

    def test_active_flag_set_to_none(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        The active flag defaults to True if it is set to NULL.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        name = 'my_example_name'
        width = 1234

        data = {
            'name': name,
            'width': width,
            'image': image_data_encoded,
            'active_flag': None,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        target_id = response.json()['target_id']
        response = get_target(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials
        )

        target_record = response.json()['target_record']
        assert target_record['active_flag'] is True

    def test_fail_status(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        When a 1x1 image is given, the status changes from 'processing' to
        failed after some time.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        name = 'my_example_name'
        width = 1234

        data = {
            'name': name,
            'width': width,
            'image': image_data_encoded,
            'active_flag': None,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        target_id = response.json()['target_id']

        for i in range(20):
            response = get_target(
                target_id=target_id,
                vuforia_server_credentials=vuforia_server_credentials
            )

            if response.json()['status'] != TargetStatuses.PROCESSING.value:
                break

            sleep(0.1)

        assert response.json()['status'] == TargetStatuses.FAILED.value
