"""
Tests for deleting targets.
"""

import pytest
from requests import codes
from requests_mock import DELETE

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    assert_vws_failure,
    get_vws_target,
    wait_for_target_processed,
)
from tests.utils import VuforiaDatabaseKeys
from vws._request_utils import target_api_request


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
        request_path = '/targets/' + target_id

        response = target_api_request(
            server_access_key=vuforia_database_keys.server_access_key,
            server_secret_key=vuforia_database_keys.server_secret_key,
            method=DELETE,
            content=b'',
            request_path=request_path,
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

        request_path = '/targets/' + target_id

        response = target_api_request(
            server_access_key=vuforia_database_keys.server_access_key,
            server_secret_key=vuforia_database_keys.server_secret_key,
            method=DELETE,
            content=b'',
            request_path=request_path,
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

        assert_vws_failure(
            response=response,
            status_code=codes.NOT_FOUND,
            result_code=ResultCodes.UNKNOWN_TARGET,
        )
