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
# 150 seconds is an arbitrary amount of time to wait.
#
# The mock does not have such a delay.
_WAIT_SECONDS = 150


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
        png_rgb: io.BytesIO,
    ) -> None:
        """
        The number of images in the processing state is returned.
        """
        # We first confirm that there are no existing processing images in the
        # summary.
        @timeout_decorator.timeout(seconds=_WAIT_SECONDS)
        def wait_for_no_processing() -> None:
            """
            Returns once there are no processing images.

            Raises:
                TimeoutError: Processing images were found in every request for
                    two minutes.
            """
            while True:
                response = database_summary(
                    vuforia_server_credentials=vuforia_server_credentials,
                    wait_seconds=0.2,
                )
                if not response.json()['processing_images']:
                    return

        wait_for_no_processing()

        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        # An image does not last long in processing.
        # Therefore, we don't wait the usual delay.
        #
        # However, as the summary endpoint is often behind,
        # we don't assume that the processing image will be detailed
        # immediately.
        # Therefore we check on a loop that it is detailed.

        @timeout_decorator.timeout(seconds=_WAIT_SECONDS)
        def wait_for_processing_image() -> requests.Response:
            """
            Returns a response from a database summary call, once there is at
                least one processing image.

            Raises:
                TimeoutError: No processing image was found in two minutes.
            """
            while True:
                response = database_summary(
                    vuforia_server_credentials=vuforia_server_credentials,
                    wait_seconds=0.1,
                )
                if response.json()['processing_images']:
                    return response

        response = wait_for_processing_image()
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
