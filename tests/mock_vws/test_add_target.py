"""
Tests for the mock of the add target endpoint.
"""

# TODO: Test both PNG and JPEG

import json

import pytest
import requests
from requests import codes
from requests_mock import POST

from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAddTarget:
    """
    Tests for the mock of the add target endpoint at `POST /targets`.
    """

    # TODO Skip this and link to an issue for deleting all targets *before*
    def test_success(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     ) -> None:
        """It is possible to get a success response."""
        date = rfc_1123_date()

        data = {
            'name': 'example_name',
            'width': 1,
        }
        content = bytes(json.dumps(data), encoding='utf-8')

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=POST,
            content=content,
            content_type='application/json',
            date=date,
            request_path='/summary',
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
        }

        response = requests.request(
            method=POST,
            url='https://vws.vuforia.com/targets',
            headers=headers,
            data=b'',
        )
        assert response.status_code == codes.OK
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
        # Test return headers, esp content-type

    def test_incorrect_content_type(self) -> None:
        pass

    # Negative, too small, too large, wrong type
    def test_width_invalid(self) -> None:
        pass

    # too short, too long, wrong type
    def test_name_invalid(self) -> None:
        pass

    def test_image_invalid(self) -> None:
        pass
