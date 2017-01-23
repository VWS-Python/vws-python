"""
Tests for getting a target record.

https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Record-Using-the-VWS-API
"""

import base64
import io

import pytest
from requests import codes

from common.constants import ResultCodes, TargetStatuses
from tests.mock_vws.utils import (
    VuforiaServerCredentials,
    add_target_to_vws,
    assert_vws_response,
    get_vws_target,
    wait_for_target_processed,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestGetRecord:
    """
    Tests for getting a target record.
    """

    def test_get_vws_target(
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
        response = get_vws_target(
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

        data = {
            'name': 'my_example_name',
            'width': 1234,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']
        response = get_vws_target(
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

        data = {
            'name': 'my_example_name',
            'width': 1234,
            'image': image_data_encoded,
            'active_flag': None,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']
        response = get_vws_target(
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

        data = {
            'name': 'my_example_name',
            'width': 1234,
            'image': image_data_encoded,
            'active_flag': None,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = get_vws_target(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials
        )

        assert response.json()['status'] == TargetStatuses.FAILED.value
