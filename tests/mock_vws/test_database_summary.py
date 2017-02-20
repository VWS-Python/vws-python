"""
Tests for the mock of the database summary endpoint.
"""

import base64
import io
from time import sleep

import pytest
import requests
import timeout_decorator
from requests import codes
from requests_mock import GET

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    assert_vws_response,
    wait_for_target_processed,
)
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request

# It takes some time for the summary endpoint to catch up with reality.
# We therefore wait to confirm that an image is detailed (or not).
# 120 seconds is an arbitrary amount of time to wait.
#
# The mock does not have such a delay.
_WAIT_SECONDS = 120


def database_summary(
    vuforia_server_credentials: VuforiaServerCredentials,
    wait_seconds: float=_WAIT_SECONDS,
) -> requests.Response:
    """
    Return the response of a request to the database summary endpoint after a
    given delay.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        wait_seconds: The number of seconds to wait before getting the database
            summary.
    """
    sleep(wait_seconds)

    return target_api_request(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        request_path='/summary',
    )


@timeout_decorator.timeout(seconds=300)
def wait_for_image_numbers(
    vuforia_server_credentials: VuforiaServerCredentials,
    active_images: int,
    inactive_images: int,
    failed_images: int,
    processing_images: int,
) -> None:
    """
    Wait up to 300 seconds (arbitrary) for the number of images in various
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
    requirements = {
        'active_images': active_images,
        'inactive_images': inactive_images,
        'failed_images': failed_images,
        'processing_images': processing_images,
    }

    while True:
        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
        )

        requirements = {
            requirement: value
            for requirement, value in requirements.items()
            if response.json()[requirement] != value
        }

        if not requirements:  # pragma: no cover
            return

        # We wait 0.2 seconds rather than less than that to decrease the number
        # of calls made to the API, to decrease the likelihood of hitting the
        # request quota.
        sleep(0.2)  # pragma: no cover


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

    def test_active_images(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        The number of images in the active state is returned.
        """
        wait_for_target_processed(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        wait_for_image_numbers(
            vuforia_server_credentials=vuforia_server_credentials,
            active_images=1,
            inactive_images=0,
            failed_images=0,
            processing_images=0,
        )

    def test_failed_images(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        The number of images with a 'fail' status is returned.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
        )

        assert response.json()['active_images'] == 0
        assert response.json()['inactive_images'] == 0
        assert response.json()['failed_images'] == 1
        assert response.json()['processing_images'] == 0

    def test_inactive_images(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb_success: io.BytesIO,
    ) -> None:
        """
        The number of images with a False active_flag and a 'success' status is
        returned.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
            'active_flag': False,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
        )

        assert response.json()['active_images'] == 0
        assert response.json()['inactive_images'] == 1
        assert response.json()['failed_images'] == 0
        assert response.json()['processing_images'] == 0

    def test_inactive_failed(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        An image with a 'failed' status does not show as inactive.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
            'active_flag': False,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials,
        )

        response = database_summary(
            vuforia_server_credentials=vuforia_server_credentials
        )

        assert response.json()['active_images'] == 0
        assert response.json()['inactive_images'] == 0
        assert response.json()['failed_images'] == 1
        assert response.json()['processing_images'] == 0


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
