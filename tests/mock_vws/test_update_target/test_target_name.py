"""
Tests for the target name field of the mock of the update target endpoint.
"""

import base64
import io

import pytest
from requests import codes

from mock_vws._constants import ResultCodes
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
class TestTargetName:
    """
    Tests for the target name field.
    """

    @pytest.mark.parametrize(
        'name', [
            'a',
            'a' * 64,
        ], ids=['Short name', 'Long name']
    )
    def test_name_valid(
        self,
        name: str,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        Names between 1 and 64 characters in length are valid.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'name': name},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        response = get_vws_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        assert response.json()['target_record']['name'] == name

    @pytest.mark.parametrize(
        'name',
        [1, '', 'a' * 65, None],
        ids=['Wrong Type', 'Empty', 'Too Long', 'None'],
    )
    def test_name_invalid(
        self,
        name: str,
        target_id: str,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        A target's name must be a string of length 0 < N < 65.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'name': name},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_existing_target_name(
        self,
        png_rgb_success: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        Only one target can have a given name.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        first_target_name = 'example_name'
        second_target_name = 'another_example_name'

        data = {
            'name': first_target_name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        first_target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=first_target_id,
        )

        other_data = {
            'name': second_target_name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=other_data,
        )

        second_target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=second_target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'name': first_target_name},
            target_id=second_target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_NAME_EXIST,
        )

    def test_same_name_given(
        self,
        png_rgb_success: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        Updating a target with its own name does not give an error.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        name = 'example'

        data = {
            'name': name,
            'width': 1,
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

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'name': name},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        response = get_vws_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        assert response.json()['target_record']['name'] == name
