"""
Tests for the mock of the database summary endpoint.
"""

from time import sleep

import pytest
import requests
import timeout_decorator
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import assert_vws_response
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


def database_summary(
    vuforia_server_credentials: VuforiaServerCredentials,
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


@timeout_decorator.timeout(seconds=200)
def wait_for_image_numbers(
    vuforia_server_credentials: VuforiaServerCredentials,
    active_images: int,
    inactive_images: int,
    failed_images: int,
    processing_images: int,
) -> None:
    """
    Wait up to 200 seconds (arbitrary) for the number of images in various
    categories to match the expected number.

    This is necessary because the database summary endpoint lags behind the
    real data.

    This is susceptible to false positives because if, for example, we expect
    no images, and the endpoint adds images with a delay, we will not know.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        active_images: The expected number of active images.
        inactive_images: The expected number of inactive images.
        failed_images: The expected number of failed images.
        processing_images: The expected number of processing images.

    Raises:
        TimeoutError: The numbers of images in various categories do not match
            within the time limit.
    """
    while True:
        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
        )

        if all(
            [
                active_images == response.json()['active_images'],
                inactive_images == response.json()['inactive_images'],
                failed_images == response.json()['failed_images'],
                processing_images == response.json()['processing_images'],
            ]
        ):
            return

        # We wait 0.2 seconds rather than less than that to decrease the number
        # of calls made to the API, to decrease the likelihood of hitting the
        # request quota.
        sleep(0.2)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDatabaseSummary:
    """
    Tests for the mock of the database summary endpoint at `GET /summary`.
    """

    def test_success(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        It is possible to get a success response.
        """
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

        wait_for_image_numbers(
            vuforia_server_credentials=vuforia_server_credentials,
            active_images=0,
            inactive_images=0,
            failed_images=0,
            processing_images=0,
        )


@pytest.mark.usefixtures('verify_mock_vuforia_inactive')
class TestInactiveProject:
    """
    Tests for inactive projects.
    """

    def test_inactive_project(
        self,
        inactive_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        The project's active state does not affect the database summary.
        """
        response = database_summary(
            vuforia_server_credentials=inactive_server_credentials,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )
