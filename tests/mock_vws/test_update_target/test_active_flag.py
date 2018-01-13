"""
Tests for the active flag of the mock of the update target endpoint.
"""

import base64
import io
from typing import Union

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
class TestActiveFlag:
    """
    Tests for the active flag parameter.
    """

    @pytest.mark.parametrize('initial_active_flag', [True, False])
    @pytest.mark.parametrize('desired_active_flag', [True, False])
    def test_active_flag(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb_success: io.BytesIO,
        initial_active_flag: bool,
        desired_active_flag: bool,
    ) -> None:
        """
        Setting the active flag to a Boolean value changes it.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
            'active_flag': initial_active_flag,
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
            data={'active_flag': desired_active_flag},
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

        new_flag = response.json()['target_record']['active_flag']
        assert new_flag == desired_active_flag

    @pytest.mark.parametrize('desired_active_flag', ['string', None])
    def test_invalid(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
        desired_active_flag: Union[str, None],
    ) -> None:
        """
        Values which are not Boolean values are not valid active flags.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'active_flag': desired_active_flag},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )
