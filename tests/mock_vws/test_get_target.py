"""
Tests for getting a target record.

https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Retrieve-a-Target-Record
"""

import base64
import io
import uuid

import pytest
from requests import codes

from mock_vws._constants import ResultCodes, TargetStatuses
from tests.mock_vws.utils import (
    add_target_to_vws,
    get_vws_target,
    wait_for_target_processed,
)
from tests.mock_vws.utils.assertions import (
    assert_vws_failure,
    assert_vws_response,
)
from tests.mock_vws.utils.authorization import VuforiaDatabaseKeys


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestGetRecord:
    """
    Tests for getting a target record.
    """

    def test_get_vws_target(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
            content_type='application/json',
        )

        target_id = response.json()['target_id']
        response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
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
        # Tracking rating may be -1 while processing.
        assert target_record['tracking_rating'] in range(-1, 6)
        assert target_record['reco_rating'] == ''

    def test_active_flag_not_set(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']
        response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        target_record = response.json()['target_record']
        assert target_record['active_flag'] is True

    def test_active_flag_set_to_none(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']
        response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        target_record = response.json()['target_record']
        assert target_record['active_flag'] is True

    def test_fail_status(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        When a 1x1 image is given, the status changes from 'processing' to
        'failed' after some time.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'my_example_name',
            'width': 1234,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        assert response.json()['status'] == TargetStatuses.FAILED.value
        # Tracking rating is 0 when status is 'failed'
        assert response.json()['target_record']['tracking_rating'] == 0

    def test_success_status(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb_success: io.BytesIO,
    ) -> None:
        """
        When a random, large enough image is given, the status changes from
        'processing' to 'success' after some time.

        The mock is much more lenient than the real implementation of VWS.
        The test image does not prove that what is counted as a success in the
        mock will be counted as a success in the real implementation.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'my_example_name',
            'width': 1234,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        assert response.json()['status'] == TargetStatuses.SUCCESS.value
        # Tracking rating is between 0 and 5 when status is 'success'
        tracking_rating = response.json()['target_record']['tracking_rating']
        assert tracking_rating in range(6)

        # The tracking rating stays stable across requests
        response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )
        new_target_record = response.json()['target_record']
        new_tracking_rating = new_target_record['tracking_rating']
        assert new_tracking_rating == tracking_rating


@pytest.mark.usefixtures('verify_mock_vuforia_inactive')
class TestInactiveProject:
    """
    Tests for inactive projects.
    """

    def test_inactive_project(
        self,
        inactive_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        The project's active state does not affect getting a target.
        """
        response = get_vws_target(
            target_id=uuid.uuid4().hex,
            vuforia_database_keys=inactive_database_keys,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.NOT_FOUND,
            result_code=ResultCodes.UNKNOWN_TARGET,
        )
