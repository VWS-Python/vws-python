"""
Tests for the mock of the add target endpoint.
"""

# TODO: Test both PNG and JPEG

import json
import uuid
from urllib.parse import urljoin

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
        content_type = 'application/json'
        request_path = '/targets'

        data = {
            'name': 'example_name_{random}'.format(random=uuid.uuid4().hex),
            'width': 1,
        }
        content = bytes(json.dumps(data), encoding='utf-8')

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=POST,
            content=content,
            content_type=content_type,
            date=date,
            request_path=request_path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
            'Content-Type': content_type,
        }

        response = requests.request(
            method=POST,
            url=urljoin('https://vws.vuforia.com/', request_path),
            headers=headers,
            data=content,
        )
        assert response.status_code == codes.OK
        assert response.json().keys() == {}
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
