"""
Tests for deleting targets.
"""

import pytest
from requests import codes
from requests_mock import DELETE

from common.constants import ResultCodes
from tests.mock_vws.utils import assert_vws_response
from vws._request_utils import target_api_request
from tests.utils import VuforiaServerCredentials


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDelete:
    """
    Tests for deleting targets.
    """

    def test_delete(self,
                    target_id: str,
                    vuforia_server_credentials: VuforiaServerCredentials,
                    ) -> None:
        """
        It is possible to delete a target.
        """
        request_path = '/targets/' + target_id

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=DELETE,
            content=b'',
            request_path=request_path,
        )

        # TODO WAIT FOR STATUS!
        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )
