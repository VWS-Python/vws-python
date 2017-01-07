"""
Tests for the mock of the add target endpoint.
"""

import base64
import io
import json
from string import hexdigits
from typing import Any, Dict
from urllib.parse import urljoin

import pytest
import requests
from _pytest.fixtures import SubRequest
from PIL import Image
from requests import codes, Response
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


def _image_file(file_format: str, color_space: str) -> io.BytesIO:
    """
    Return an image file in the given format and color space.

    Args:
        file_format: See
            http://pillow.readthedocs.io/en/3.1.x/handbook/image-file-formats.html
        color_space: One of "L", "RGB", or "CMYK". "L" means greyscale.
    """
    image_buffer = io.BytesIO()
    width = 1
    height = 1
    image = Image.new(color_space, (width, height))
    image.save(image_buffer, file_format)
    image_buffer.seek(0)
    return image_buffer


@pytest.fixture
def png_rgb() -> io.BytesIO:
    """
    Return a PNG file in the RGB color space.
    """
    return _image_file(file_format='PNG', color_space='RGB')


@pytest.fixture
def png_greyscale() -> io.BytesIO:
    """
    Return a PNG file in the greyscale color space.
    """
    return _image_file(file_format='PNG', color_space='L')


@pytest.fixture
def jpeg_cmyk() -> io.BytesIO:
    """
    Return a PNG file in the CMYK color space.
    """
    return _image_file(file_format='JPEG', color_space='CMYK')


@pytest.fixture
def jpeg_rgb() -> io.BytesIO:
    """
    Return a JPEG file in the RGB color space.
    """
    return _image_file(file_format='JPEG', color_space='RGB')


@pytest.fixture
def tiff_rgb() -> io.BytesIO:
    """
    Return a TIFF file in the RGB color space.

    This is given as an option which is not supported by Vuforia as Vuforia
    supports only JPEG and PNG files.
    """
    return _image_file(file_format='TIFF', color_space='RGB')


@pytest.fixture(params=['png_rgb', 'jpeg_rgb', 'png_greyscale'])
def image_file(request: SubRequest) -> io.BytesIO:
    """
    Return an image file.
    """
    return request.getfixturevalue(request.param)


def add_target(
    vuforia_server_credentials: VuforiaServerCredentials,
    data: Dict[str, Any],
    content_type: str='application/json',
) -> requests.Response:
    """
    Helper to make a request to the endpoint to add a target.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        data: The data to send, in JSON format, to the endpoint.
        content_type: The `Content-Type` header to use.

    Returns:
        The response returned by the API.
    """
    date = rfc_1123_date()
    request_path = '/targets'

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

    return response


def assert_success(response: Response) -> None:
    """
    Assert that the given response is a success response for adding a
    target.

    Raises:
        AssertionError: The given response is not a valid success response
            for adding a target.
    """
    assert_vws_response(
        response=response,
        status_code=codes.CREATED,
        result_code=ResultCodes.TARGET_CREATED,
    )
    expected_keys = {'result_code', 'transaction_id', 'target_id'}
    assert response.json().keys() == expected_keys
    assert_valid_target_id(target_id=response.json()['target_id'])


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestContentTypes:
    """
    Tests for the `Content-Type` header.
    """

    @pytest.mark.parametrize('content_type', [
        # This is the documented required content type:
        'application/json',
        # Other content types also work.
        'other/content_type',
        '',
    ], ids=['Documented Content-Type', 'Undocumented Content-Type', 'Empty'])
    def test_content_types(self,
                           vuforia_server_credentials:
                           VuforiaServerCredentials,
                           png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                           content_type: str,
                           ) -> None:
        """
        Any `Content-Type` header is allowed.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type=content_type,
        )

        assert_success(response=response)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestMissingData:
    """
    Tests for giving incomplete data.
    """

    @pytest.mark.parametrize('data_to_remove', ['name', 'width', 'image'])
    def test_missing_data(self,
                          vuforia_server_credentials:
                          VuforiaServerCredentials,
                          png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                          data_to_remove: str,
                          ) -> None:
        """
        `name`, `width` and `image` are all required.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
        }
        data.pop(data_to_remove)

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestWidth:
    """
    Tests for the target width field.
    """

    @pytest.mark.parametrize(
        'width',
        [-1, '10'],
        ids=['Negative', 'Wrong Type'],
    )
    def test_width_invalid(self,
                           vuforia_server_credentials:
                           VuforiaServerCredentials,
                           png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                           width: Any) -> None:
        """
        The width must be a non-negative number.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': width,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    @pytest.mark.parametrize('width', [0, 0.1],
                             ids=['Zero width', 'Float width'])
    def test_width_valid(self,
                         vuforia_server_credentials:
                         VuforiaServerCredentials,
                         png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                         width: Any) -> None:
        """
        Non-negative numbers are valid widths.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': width,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        assert_success(response=response)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestTargetName:
    """
    Tests for the target name field.
    """

    @pytest.mark.parametrize('name', [
        'a',
        'a' * 64,
    ], ids=['Short name', 'Long name'])
    def test_name_valid(self,
                        name: str,
                        png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                        vuforia_server_credentials: VuforiaServerCredentials
                        ) -> None:
        """
        Names between 1 and 64 characters in length are valid.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        assert_success(response=response)

    @pytest.mark.parametrize(
        'name',
        [1, '', 'a' * 65],
        ids=['Wrong Type', 'Empty', 'Too Long'],
    )
    def test_name_invalid(self,
                          name: str,
                          png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                          vuforia_server_credentials: VuforiaServerCredentials
                          ) -> None:
        """
        A target's name must be a string of length 0 < N < 65.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_existing_target_name(self,
                                  png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                                  vuforia_server_credentials:
                                  VuforiaServerCredentials) -> None:
        """
        Only one target can have a given name.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
        }

        add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_NAME_EXIST,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestImage:
    """
    Tests for the image parameter.

    The specification for images is documented in "Supported Images" on
    https://library.vuforia.com/articles/Training/Image-Target-Guide
    """

    def test_image_valid(self,
                         vuforia_server_credentials: VuforiaServerCredentials,
                         image_file: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                         ) -> None:
        """
        JPEG and PNG files in the RGB and greyscale color spaces are
        allowed.
        """
        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        assert_success(response=response)

    def test_invalid_type(self,
                          tiff_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                          vuforia_server_credentials: VuforiaServerCredentials,
                          ) -> None:
        """
        A `BAD_REQUEST` response is returned if an image which is not a JPEG
        or PNG file is given.
        """
        image_data = tiff_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.BAD_IMAGE,
        )

    def test_wrong_color_space(self,
                               jpeg_cmyk: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                               vuforia_server_credentials:
                               VuforiaServerCredentials,
                               ) -> None:
        """
        A `BAD_REQUEST` response is returned if an image which is not in the
        greyscale or RGB color space.
        """
        image_data = jpeg_cmyk.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.BAD_IMAGE,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestNotMandatoryFields:
    """
    Tests for passing data which is not mandatory to the endpoint.
    """

    def test_invalid_extra_data(self,
                                vuforia_server_credentials:
                                VuforiaServerCredentials,
                                png_rgb: io.BytesIO,  # noqa: E501 pylint: disable=redefined-outer-name
                                ) -> None:
        """
        A `BAD_REQUEST` response is returned when unexpected data is given.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
            'extra_thing': 1,
        }

        response = add_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )
