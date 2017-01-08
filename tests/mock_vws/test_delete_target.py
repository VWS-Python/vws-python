"""
Tests for deleting targets.
"""

import pytest
from requests import codes
from requests_mock import DELETE

from common.constants import ResultCodes
from tests.mock_vws.utils import assert_vws_failure
from vws._request_utils import target_api_request
from tests.utils import VuforiaServerCredentials


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDelete:
    """
    Tests for deleting targets.
    """

    def test_no_wait(self,
                     target_id: str,
                     vuforia_server_credentials: VuforiaServerCredentials,
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
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=DELETE,
            content=b'',
            request_path=request_path,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_STATUS_PROCESSING,
        )
