"""
Tests for the mock of the target summary endpoint.
"""

import base64
import datetime
import io

import pytest
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import add_target_to_vws, assert_vws_response
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestTargetSummary:
    """
    Tests for the target summary endpoint.
    """

    def test_target_summary(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        A target summary is returned.
        """
        name = 'example target name 1234'

        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        date_before_add_target = datetime.datetime.now().date()

        target_response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data={
                'name': name,
                'width': 1,
                'image': image_data_encoded,
            }
        )

        target_id = target_response.json()['target_id']

        date_after_add_target = datetime.datetime.now().date()

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/summary/' + target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        expected_keys = {
            'status',
            'result_code',
            'transaction_id',
            'database_name',
            'target_name',
            'upload_date',
            'active_flag',
            'tracking_rating',
            'total_recos',
            'current_month_recos',
            'previous_month_recos',
        }

        assert response.json().keys() == expected_keys
        assert response.json()['status'] == 'processing'
        assert response.json()['database_name'] == (
            vuforia_server_credentials.database_name
        )
        assert response.json()['target_name'] == name

        # In case the date changes while adding a target
        # we allow the date before and after adding the target.
        assert response.json()['upload_date'] in (
            date_before_add_target.strftime('%Y-%m-%d'),
            date_after_add_target.strftime('%Y-%m-%d'),
        )

        get_target_response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/targets/' + target_id,
        )

        target_record = get_target_response.json()['target_record']
        tracking_rating = target_record['tracking_rating']
        assert response.json()['tracking_rating'] == tracking_rating

    @pytest.mark.parametrize('active_flag', [True, False])
    def test_active_flag(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
        active_flag: bool,
    ) -> None:
        """
        The active flag of the target is returned.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        target_response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data={
                'name': 'example',
                'width': 1,
                'image': image_data_encoded,
                'active_flag': active_flag,
            }
        )

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/summary/' + target_response.json()['target_id'],
        )

        assert response.json()['active_flag'] == active_flag
