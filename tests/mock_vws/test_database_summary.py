"""
Tests for the mock of the database summary endpoint.
"""

import pytest
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    assert_vws_response,
    get_vws_target,
    wait_for_target_processed,
)
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDatabaseSummary:
    """
    Tests for the mock of the database summary endpoint at `GET /summary`.
    """

    def test_success(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """It is possible to get a success response."""
        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/summary',
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        assert response.json().keys() == {
            'active_images',
            'current_month_recos',
            'failed_images',
            'inactive_images',
            'name',
            'previous_month_recos',
            'processing_images',
            'reco_threshold',
            'request_quota',
            'request_usage',
            'result_code',
            'target_quota',
            'total_recos',
            'transaction_id',
        }

        assert response.json()['name'] == (
            vuforia_server_credentials.database_name
        )

        assert response.json()['active_images'] == 0
        assert response.json()['inactive_images'] == 0
        assert response.json()['failed_images'] == 0
        assert response.json()['processing_images'] == 0

    def test_processing_images(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        The number of images in the processing state is returned.
        """
        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/summary',
        )

        assert response.json()['active_images'] == 0
        assert response.json()['inactive_images'] == 0
        assert response.json()['failed_images'] == 0
        assert response.json()['processing_images'] == 1

    def test_active_images(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        The number of images in the processing state is returned.
        """
        wait_for_target_processed(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=GET,
            content=b'',
            request_path='/summary',
        )

        assert response.json()['active_images'] == 1
        assert response.json()['inactive_images'] == 0
        assert response.json()['failed_images'] == 0
        assert response.json()['processing_images'] == 0
