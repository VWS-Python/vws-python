"""
Tests for the mock of the add target endpoint.
"""

# TODO: Test both PNG and JPEG
# TODO: Document that "image" is mandatory, despite what the docs say
# TODO: Test missing width, others
# TODO: Test not a PNG, JPEG
# TODO: Handle 'RequestQuotaReached'

import base64
import io
import json
import random
import uuid
from urllib.parse import urljoin
from typing import Any

import pytest
import requests
from _pytest.fixtures import SubRequest
from PIL import Image
from requests import codes
from requests_mock import POST

from common.constants import ResultCodes
from tests.mock_vws.utils import is_valid_transaction_id, assert_vws_failure
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


def assert_valid_target_id(target_id: str) -> None:
    pass


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
    def image_file(self, request: SubRequest) -> io.BytesIO:
        return request.getfixturevalue(request.param)

    # TODO Skip this and link to an issue for deleting all targets *before*
    # TODO: Send Bad JSON
    @pytest.mark.parametrize('content_type', [
        # This is the documented required content type:
        'application/json',
        # Other content types also work.
        'other/content_type',
    ])
    def test_success(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     image_file: io.BytesIO,
                     content_type: str) -> None:
        """It is possible to get a success response."""
        date = rfc_1123_date()
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
        assert_valid_target_id(target_id=response.json()['target_id'])

    @pytest.mark.parametrize('width', [-1, 'wrong_type'])
    def test_width_invalid(self,
                           vuforia_server_credentials:
                           VuforiaServerCredentials,
                           image_file: io.BytesIO,
                           width: Any) -> None:
        content_type = 'application/json'
        date = rfc_1123_date()
        request_path = '/targets'

        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name_{random}'.format(random=uuid.uuid4().hex),
            'width': width,
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

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    @pytest.mark.parametrize('data_to_remove', ['name', 'width', 'image'])
    def test_missing_data(self, vuforia_server_credentials,
                          image_file,
                          data_to_remove,
                          ) -> None:
        content_type = 'application/json'
        date = rfc_1123_date()
        request_path = '/targets'

        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name_{random}'.format(random=uuid.uuid4().hex),
            'width': 1,
            'image': image_data_encoded,
        }
        data.pop(data_to_remove)
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

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    # too short, too long, wrong type
    def test_name_invalid(self) -> None:
        pass

    # Not JPEG/PNG
    # Not RGB/greyscale
    # > 2mb
    def test_image_invalid(self) -> None:
        # See https://library.vuforia.com/articles/Training/Image-Target-Guide
        pass

    # Test adding random extra field.
    # If there's an error, have a test for that.
    # If there's an error, have a test which allows

    # Test missing image
    # Test missing width
    # Test missing name
