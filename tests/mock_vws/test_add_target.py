"""
Tests for the mock of the add target endpoint.
"""

# TODO: Test both PNG and JPEG
# TODO: Document that "image" is mandatory, despite what the docs say

import base64
import io
import json
import random
import uuid
from urllib.parse import urljoin

import pytest
import requests
from PIL import Image
from requests import codes
from requests_mock import POST

from common.constants import ResultCodes
from tests.mock_vws.utils import is_valid_transaction_id
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAddTarget:
    """
    Tests for the mock of the add target endpoint at `POST /targets`.
    """

    @pytest.fixture
    def png_file(self) -> io.BytesIO:
        image_buffer = io.BytesIO()

        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        width = 1
        height = 1

        image = Image.new('RGB', (width, height), color=(red, green, blue))
        image.save(image_buffer, 'PNG')
        image_buffer.seek(0)
        return image_buffer

    @pytest.fixture(params=['png_file'])
    # Have a factory which takes details
    def image_file(self, request) -> io.BytesIO:
        return request.getfixturevalue(request.param)

    # TODO Skip this and link to an issue for deleting all targets *before*
    # TODO: Send Bad JSON
    def test_success(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     image_file) -> None:
        """It is possible to get a success response."""
        date = rfc_1123_date()
        content_type = 'application/json'
        request_path = '/targets'

        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name_{random}'.format(random=uuid.uuid4().hex),
            'width': 1,
            'image': image_data_encoded,
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
        assert response.status_code == codes.CREATED
        expected_keys = {'result_code', 'transaction_id', 'target_id'}
        assert response.json().keys() == expected_keys
        assert response.headers['Content-Type'] == 'application/json'
        expected_result_code = ResultCodes.TARGET_CREATED.value
        assert response.json()['result_code'] == expected_result_code
        assert is_valid_transaction_id(response.json()['transaction_id'])
        # TODO: assert_valid_target_id(response.json()['target_id'])

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
