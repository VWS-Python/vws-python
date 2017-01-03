"""
Tests for the mock of the add target endpoint.
"""

# TODO: Document that "image" is mandatory, despite what the docs say
# TODO: Handle 'RequestQuotaReached'

import base64
import io
import json
import random
import uuid
from string import hexdigits
from typing import Any
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


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAddTarget:
    """
    Tests for the mock of the add target endpoint at `POST /targets`.
    """

    @pytest.fixture
    def png_file(self) -> io.BytesIO:
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
    def image_file(self, request: SubRequest) -> io.BytesIO:
        """
        Return an image file.
        """
        return request.getfixturevalue(request.param)

    @pytest.mark.parametrize('content_type', [
        # This is the documented required content type:
        'application/json',
        # Other content types also work.
        'other/content_type',
    ])
    def test_created(self,
                     vuforia_server_credentials: VuforiaServerCredentials,
                     image_file: io.BytesIO,
                     content_type: str) -> None:
        """It is possible to get a `TargetCreated` response."""
        date = rfc_1123_date()
        request_path = '/targets'

        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
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
                           png_file: io.BytesIO,
                           width: Any) -> None:
        """
        XXX
        """
        content_type = 'application/json'
        date = rfc_1123_date()
        request_path = '/targets'

        image_data = png_file.read()
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

    @pytest.mark.parametrize(
        'name',
        [1, '', 'a' * 65],
        ids=['Wrong Type', 'Empty', 'Too Long'],
    )
    def test_name_invalid(self,
                          name: str,
                          png_file: io.BytesIO,
                          vuforia_server_credentials: VuforiaServerCredentials
                          ) -> None:
        date = rfc_1123_date()
        request_path = '/targets'
        content_type = 'application/json'

        image_data = png_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': name,
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
        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )


class TestInvalidImage:
    # See https://library.vuforia.com/articles/Training/Image-Target-Guide

    # Not JPEG/PNG
    def test_invalid_type(self) -> None:
        pass

    # > 2mb
    def test_too_large(self) -> None:
        pass

    # Not RGB/greyscale
    def test_wrong_colour_space(self) -> None:
        pass


class TestNotMandatoryFields:

    def test_invalid_extra_data(self,
                                vuforia_server_credentials:
                                VuforiaServerCredentials,
                                image_file: io.BytesIO,
                                ) -> None:
        """XXX"""
        date = rfc_1123_date()
        request_path = '/targets'
        content_type = 'application/json'

        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name_{random}'.format(random=uuid.uuid4().hex),
            'width': 1,
            'image': image_data_encoded,
            'extra_thing': 1,
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

    def test_valid_extra_data(self) -> None:
        active_flag = True
        application_metadata = 'a' # something base64 encoded
        pass

    def test_invalid_active_flag(self) -> None:
        pass

    def test_invalid_application_metadata(self) -> None:
        pass
