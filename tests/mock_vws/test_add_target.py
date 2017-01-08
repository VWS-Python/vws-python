"""
Tests for the mock of the add target endpoint.
"""

import base64
import io
from string import hexdigits
from typing import Any

import pytest
from requests import Response, codes

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    assert_vws_failure,
    assert_vws_response,
)
from tests.utils import VuforiaServerCredentials


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
                           png_rgb: io.BytesIO,
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

        response = add_target_to_vws(
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
                          png_rgb: io.BytesIO,
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

        response = add_target_to_vws(
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
                           png_rgb: io.BytesIO,
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

        response = add_target_to_vws(
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
                         png_rgb: io.BytesIO,
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

        response = add_target_to_vws(
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
                        png_rgb: io.BytesIO,
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

        response = add_target_to_vws(
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
                          png_rgb: io.BytesIO,
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

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_existing_target_name(self,
                                  png_rgb: io.BytesIO,
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

        add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        response = add_target_to_vws(
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
                         image_file: io.BytesIO,
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

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type='application/json',
        )

        assert_success(response=response)

    def test_invalid_type(self,
                          tiff_rgb: io.BytesIO,
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

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.BAD_IMAGE,
        )

    def test_wrong_color_space(self,
                               jpeg_cmyk: io.BytesIO,
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

        response = add_target_to_vws(
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
                                png_rgb: io.BytesIO,
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

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )
