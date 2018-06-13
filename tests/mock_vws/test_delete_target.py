"""
Tests for deleting targets.
"""

import pytest
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    delete_target,
    get_vws_target,
    wait_for_target_processed,
)
from tests.mock_vws.utils.assertions import (
    assert_vws_failure,
    assert_vws_response,
)
from tests.mock_vws.utils.authorization import VuforiaDatabaseKeys


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDelete:
    """
    Tests for deleting targets.
    """

    def test_no_wait(
        self,
        target_id: str,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        When attempting to delete a target immediately after creating it, a
        `FORBIDDEN` response is returned.

        This is because the target goes into a processing state.

        There is a race condition here - if the target goes into a success or
        fail state before the deletion attempt.
        """
        response = delete_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_STATUS_PROCESSING,
        )

    def test_processed(
        self,
        target_id: str,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        When a target has finished processing, it can be deleted.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = delete_target(
            vuforia_database_keys=vuforia_database_keys,
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

        assert_vws_failure(
            response=response,
            status_code=codes.NOT_FOUND,
            result_code=ResultCodes.UNKNOWN_TARGET,
        )
