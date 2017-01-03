"""
Tests for the mock of the add target endpoint.
"""

import base64
import io
import json
import random
from string import hexdigits
from typing import Any, Union
from urllib.parse import urljoin

import pytest
import requests
from _pytest.fixtures import SubRequest
from PIL import Image
from requests import codes
from requests_mock import POST

from common.constants import ResultCodes
from tests.mock_vws.utils import assert_vws_failure, assert_vws_response
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


def assert_valid_target_id(target_id: str) -> None:
    """
    Assert that a given Target ID is in a valid format.

    Args:
        target_id: The Target ID to check.

    Raises:
        AssertionError: The Target ID is not in a valid format.
    """
    assert len(target_id) == 32
    assert all(char in hexdigits for char in target_id)


@pytest.fixture
def png_file() -> io.BytesIO:
    """
    Return a random coloured, 1x1 PNG, RGB file.
    """
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
def image_file(request: SubRequest) -> io.BytesIO:
    """
    Return an image file.
    """
    return request.getfixturevalue(request.param)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAddTarget:
    """
    Tests for the mock of the add target endpoint at `POST /targets`.
    """

    @pytest.mark.parametrize('content_type', [
        # This is the documented required content type:
        'application/json',
        # Other content types also work.
        'other/content_type',
    ], ids=['Documented Content-Type', 'Undocumented Content-Type'])
    @pytest.mark.parametrize('name', [
        'a',
        'a' * 64,
    ], ids=['Short name', 'Long name'])
    @pytest.mark.parametrize('width', [0, 0.1],
                             ids=['Zero width', 'Float width'])
    def test_created(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     image_file: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                     content_type: str,
                     name: str,
                     width: Union[int, float],
                     ) -> None:
        """It is possible to get a `TargetCreated` response."""
        date = rfc_1123_date()
        request_path = '/targets'

        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': name,
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
        assert_vws_response(
            response=response,
            status_code=codes.CREATED,
            result_code=ResultCodes.TARGET_CREATED,
        )
        expected_keys = {'result_code', 'transaction_id', 'target_id'}
        assert response.json().keys() == expected_keys
        assert_valid_target_id(target_id=response.json()['target_id'])

    def test_invalid_json(self,
                          vuforia_server_credentials: VuforiaServerCredentials,
                          ) -> None:
        """
        A `Fail` result is returned when the data given is not valid JSON.
        """
        content_type = 'application/json'
        date = rfc_1123_date()
        request_path = '/targets'

        content = b'a'

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

    @pytest.mark.parametrize(
        'width',
        [-1, '10'],
        ids=['Negative', 'Wrong Type'],
    )
    def test_width_invalid(self,
                           vuforia_server_credentials:
                           VuforiaServerCredentials,
                           png_file: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name

                           width: Any) -> None:
        """
        The width must be a non-negative number.
        """
        content_type = 'application/json'
        date = rfc_1123_date()
        request_path = '/targets'

        image_data = png_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
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
    def test_missing_data(self,
                          vuforia_server_credentials:
                          VuforiaServerCredentials,
                          png_file: io.BytesIO,
                          data_to_remove: str,
                          ) -> None:
        content_type = 'application/json'
        date = rfc_1123_date()
        request_path = '/targets'

        image_data = png_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
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
