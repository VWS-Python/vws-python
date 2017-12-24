"""
Tests for the mock of the get duplicates endpoint.
"""

import base64
import io
import uuid

import pytest
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    assert_vws_response,
    wait_for_target_processed,
)
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDuplicates:
    """
    Tests for the mock of the target duplicates endpoint.
    """

    def test_duplicates(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        high_quality_image: io.BytesIO,
        png_greyscale: io.BytesIO,
    ) -> None:
        """
        Target IDs of similar targets are returned.

        In the mock, "similar" means that the images are exactly the same.
        """
        image_data = high_quality_image.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        different = png_greyscale.read()
        different_data_encoded = base64.b64encode(different).decode('ascii')

        original_data = {
            'name': str(uuid.uuid4()),
            'width': 1,
            'image': image_data_encoded,
        }

        similar_data = {
            'name': str(uuid.uuid4()),
            'width': 1,
            'image': image_data_encoded,
        }

        different_data = {
            'name': str(uuid.uuid4()),
            'width': 1,
            'image': different_data_encoded,
        }

        original_add_resp = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=original_data,
        )

        similar_add_resp = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=similar_data,
        )

        different_add_resp = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=different_data,
        )

        original_target_id = original_add_resp.json()['target_id']
        similar_target_id = similar_add_resp.json()['target_id']
        different_target_id = different_add_resp.json()['target_id']

        for target_id in {
            original_target_id,
            similar_target_id,
            different_target_id,
        }:
            wait_for_target_processed(
                vuforia_server_credentials=vuforia_server_credentials,
                target_id=target_id,
            )

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/duplicates/' + original_target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        expected_keys = {
            'result_code',
            'transaction_id',
            'similar_targets',
        }

        assert response.json().keys() == expected_keys

        assert response.json()['similar_targets'] == [similar_target_id]

    def test_processing(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_greyscale: io.BytesIO,
    ) -> None:
        """
        Targets are not duplicates while they are being processed.
        """
        image_data = png_greyscale.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        original_data = {
            'name': str(uuid.uuid4()),
            'width': 1,
            'image': image_data_encoded,
        }

        similar_data = {
            'name': str(uuid.uuid4()),
            'width': 1,
            'image': image_data_encoded,
        }

        original_add_resp = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=original_data,
        )

        similar_add_resp = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=similar_data,
        )

        original_target_id = original_add_resp.json()['target_id']
        similar_target_id = similar_add_resp.json()['target_id']

        for target_id in {
            original_target_id,
            similar_target_id,
        }:
            wait_for_target_processed(
                vuforia_server_credentials=vuforia_server_credentials,
                target_id=target_id,
            )

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/duplicates/' + original_target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        assert response.json()['similar_targets'] == []
