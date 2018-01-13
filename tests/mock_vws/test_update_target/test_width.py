"""
Tests for the width parameter of the mock of the update target endpoint.
"""

from typing import Any

import pytest
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    assert_vws_failure,
    assert_vws_response,
    get_vws_target,
    update_target,
    wait_for_target_processed,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestWidth:
    """
    Tests for the target width field.
    """

    @pytest.mark.parametrize(
        'width',
        [-1, '10', None, 0],
        ids=['Negative', 'Wrong Type', 'None', 'Zero'],
    )
    def test_width_invalid(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        width: Any,
        target_id: str,
    ) -> None:
        """
        The width must be a number greater than zero.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = get_vws_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        original_width = response.json()['target_record']['width']

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'width': width},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

        response = get_vws_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        new_width = response.json()['target_record']['width']

        assert new_width == original_width

    def test_width_valid(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        Positive numbers are valid widths.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        width = 0.01

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'width': width},
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

        new_width = response.json()['target_record']['width']
        assert new_width == width
