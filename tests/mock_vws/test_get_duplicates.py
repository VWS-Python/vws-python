"""
Tests for the mock of the get duplicates endpoint.
"""

import uuid

import pytest
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import assert_vws_response
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDuplicates:
    """
    Tests for the mock of the target duplicates endpoint.
    """

    def test_no_duplicates(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        If there are no similar images to the given target, an empty list is
        returned.
        """
        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/duplicates/' + target_id,
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

        assert response.json()['similar_targets'] == []

    def test_duplicates(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
        png_greyscale: io.BytesIO,
    ) -> None:
        """
        XXX
        """
        first_target = 'X'

        similar_target = 'X'

        different_target = 'X'

        image_data = png_rgb.read()
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

        add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=original_data,
        )

        add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=similar_data,
        )

        add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=different_data,
        )

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/duplicates/' + target_id,
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
