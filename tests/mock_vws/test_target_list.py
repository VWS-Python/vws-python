"""
Tests for the mock of the target list endpoint.
"""

import pytest
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import list_targets
from tests.mock_vws.utils.assertions import assert_vws_response
from tests.mock_vws.utils.authorization import VuforiaDatabaseKeys


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
        response = list_targets(vuforia_database_keys=vuforia_database_keys)
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
        response = list_targets(vuforia_database_keys=vuforia_database_keys)
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
        response = list_targets(vuforia_database_keys=inactive_database_keys)
        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )
