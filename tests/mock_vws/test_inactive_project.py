"""
Tests for inactive projects.
"""

import base64
import io
import json

import pytest

from tests.mock_vws.utils import assert_vws_failure, Endpoint
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


@pytest.mark.usefixtures('verify_mock_vuforia_inactive')
class TestInactiveProject:
    """
    Tests for inactive projects.
    """

    def test_inactive_project(
        self,
        add_target: Endpoint,
        vuforia_inactive_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        A response for an inactive project describes that the project is
        inactive.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
        }
        endpoint = add_target
        response = target_api_request(
            access_key=vuforia_inactive_server_credentials.access_key,
            secret_key=vuforia_inactive_server_credentials.secret_key,
            method=endpoint.method,
            content=bytes(json.dumps(data), encoding='utf-8'),
            request_path=endpoint.example_path,
        )

        assert_vws_failure(
            response=response,
            status_code='X',
            result_code='X',
        )
