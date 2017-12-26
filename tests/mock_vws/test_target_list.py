"""
Tests for the mock of the target list endpoint.
"""

import pytest
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import assert_vws_response
from tests.utils import VuforiaDatabaseKeys
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestTargetList:
    """
    Tests for the mock of the database summary endpoint at `/summary`.
    """

    def test_success(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        It is possible to get a success response.
        """
        response = target_api_request(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=GET,
            content=b'',
            request_path='/targets',
        )
        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )
        expected_keys = {'result_code', 'transaction_id', 'results'}
        assert response.json().keys() == expected_keys
        assert response.json()['results'] == []

    def test_includes_targets(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        Targets in the database are returned in the list.
        """
        response = target_api_request(
            access_key=vuforia_database_keys.server_access_key,
            secret_key=vuforia_database_keys.server_secret_key,
            method=GET,
            content=b'',
            request_path='/targets',
        )
        assert response.json()['results'] == [target_id]


@pytest.mark.usefixtures('verify_mock_vuforia_inactive')
class TestInactiveProject:
    """
    Tests for inactive projects.
    """

    def test_inactive_project(
        self,
        inactive_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        The project's active state does not affect the target list.
        """
        response = target_api_request(
            access_key=inactive_database_keys.server_access_key,
            secret_key=inactive_database_keys.server_secret_key,
            method=GET,
            content=b'',
            request_path='/targets',
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )
