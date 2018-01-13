"""
Tests for success cases of the mock of the update target endpoint.
"""

import base64
import io

import pytest
from requests import codes

from mock_vws._constants import ResultCodes, TargetStatuses
from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    add_target_to_vws,
    assert_vws_failure,
    assert_vws_response,
    get_vws_target,
    update_target,
    wait_for_target_processed,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestSuccess:
    """
    Tests for the base cases of updating targets.
    """

    @pytest.mark.parametrize(
        'content_type',
        [
            # This is the documented required content type:
            'application/json',
            # Other content types also work.
            'other/content_type',
            '',
        ],
        ids=[
            'Documented Content-Type',
            'Undocumented Content-Type',
            'Empty',
        ]
    )
    def test_content_types(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
        content_type: str,
    ) -> None:
        """
        The `Content-Type` header does not change the response.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'name': 'Adam'},
            target_id=target_id,
            content_type=content_type
        )

        # Code is FORBIDDEN because the target is processing.
        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_STATUS_NOT_SUCCESS,
        )

    def test_no_fields_given(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        No data fields are required.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        assert response.json().keys() == {'result_code', 'transaction_id'}

        response = get_vws_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        # Targets go back to processing after being updated.
        assert response.json()['status'] == TargetStatuses.PROCESSING.value

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = get_vws_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        assert response.json()['status'] == TargetStatuses.SUCCESS.value
