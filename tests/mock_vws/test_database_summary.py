"""
Tests for the mock of the database summary endpoint.
"""

import io

import pytest
import requests
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import assert_vws_response, wait_for_target_processed
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


def database_summary(
    vuforia_server_credentials: VuforiaServerCredentials
) -> requests.Response:
    """
    Return the response of a request to the database summary endpoint.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
    """
    return target_api_request(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        request_path='/summary',
    )


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
        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
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
        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
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

        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
        )

        assert response.json()['active_images'] == 1
        assert response.json()['inactive_images'] == 0
        assert response.json()['failed_images'] == 0
        assert response.json()['processing_images'] == 0

    def test_failed_images(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        The number of images with a 'fail' status is returned.
        """

    def test_inactive_images(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb_success: io.BytesIO,
    ) -> None:
        """
        The number of images with a False active_flag and a 'success' status is
        returned.
        """
