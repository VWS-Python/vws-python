"""
Tests for the mock of the database summary endpoint.
"""

import base64
import io
import uuid
from time import sleep

import pytest
import timeout_decorator
from requests import codes

from mock_vws import MockVWS
from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    database_summary,
    delete_target,
    wait_for_target_processed,
)
from tests.mock_vws.utils.assertions import assert_vws_response
from tests.mock_vws.utils.authorization import VuforiaDatabaseKeys


@timeout_decorator.timeout(seconds=300)
def wait_for_image_numbers(
    vuforia_database_keys: VuforiaDatabaseKeys,
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
        vuforia_database_keys: The credentials to use to connect to
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
            vuforia_database_keys=vuforia_database_keys,
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
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        It is possible to get a success response.
        """
        response = database_summary(
            vuforia_database_keys=vuforia_database_keys,
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

        response_name = response.json()['name']
        assert response_name == vuforia_database_keys.database_name

        wait_for_image_numbers(
            vuforia_database_keys=vuforia_database_keys,
            active_images=0,
            inactive_images=0,
            failed_images=0,
            processing_images=0,
        )

    def test_active_images(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        The number of images in the active state is returned.
        """
        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        wait_for_image_numbers(
            vuforia_database_keys=vuforia_database_keys,
            active_images=1,
            inactive_images=0,
            failed_images=0,
            processing_images=0,
        )

    def test_failed_images(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        The number of images with a 'failed' status is returned.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        wait_for_image_numbers(
            vuforia_database_keys=vuforia_database_keys,
            active_images=0,
            inactive_images=0,
            failed_images=1,
            processing_images=0,
        )

    def test_inactive_images(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        wait_for_image_numbers(
            vuforia_database_keys=vuforia_database_keys,
            active_images=0,
            inactive_images=1,
            failed_images=0,
            processing_images=0,
        )

    def test_inactive_failed(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        wait_for_image_numbers(
            vuforia_database_keys=vuforia_database_keys,
            active_images=0,
            inactive_images=0,
            failed_images=1,
            processing_images=0,
        )

    def test_deleted(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        Deleted targets are not shown in the summary.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        delete_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        wait_for_image_numbers(
            vuforia_database_keys=vuforia_database_keys,
            active_images=0,
            inactive_images=0,
            failed_images=0,
            processing_images=0,
        )


class TestProcessingImages:
    """
    Tests for processing images.

    These tests are run only on the mock, and not the real implementation.

    This is because the real implementation is not reliable.
    This is a documented difference between the mock and the real
    implementation.
    """

    def test_processing_images(
        self,
        png_rgb_success: io.BytesIO,
    ) -> None:
        """
        The number of images in the processing state is returned.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        with MockVWS() as mock:
            vuforia_database_keys = VuforiaDatabaseKeys(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
                database_name=mock.database_name,
                client_access_key=uuid.uuid4().hex,
                client_secret_key=uuid.uuid4().hex,
            )

            add_target_to_vws(
                vuforia_database_keys=vuforia_database_keys,
                data=data,
            )

            wait_for_image_numbers(
                vuforia_database_keys=vuforia_database_keys,
                active_images=0,
                inactive_images=0,
                failed_images=0,
                processing_images=1,
            )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestQuotas:
    """
    Tests for the mock of the database summary endpoint at `GET /summary`.
    """

    def test_quotas(self, vuforia_database_keys: VuforiaDatabaseKeys) -> None:
        """
        Quotas are included in the database summary.
        These match the quotas given for a free license.
        """
        response = database_summary(
            vuforia_database_keys=vuforia_database_keys,
        )

        assert response.json()['target_quota'] == 1000
        assert response.json()['request_quota'] == 100000
        assert response.json()['reco_threshold'] == 1000


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
        The project's active state does not affect the database summary.
        """
        response = database_summary(
            vuforia_database_keys=inactive_database_keys,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )
