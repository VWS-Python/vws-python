"""
Tests for the mock of the add target endpoint.
"""

import base64
import binascii
import io
from string import hexdigits
from typing import Any, Union

import pytest
from requests import Response, codes

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    assert_vws_failure,
    assert_vws_response,
)
from tests.utils import VuforiaServerCredentials


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
    target_id = response.json()['target_id']
    assert len(target_id) == 32
    assert all(char in hexdigits for char in target_id)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestContentTypes:
    """
    Tests for the `Content-Type` header.
    """

    @pytest.mark.parametrize(
        'content_type',
        [
            # This is the documented required content type:
            'application/json',
            # Other content types also work.
            'other/content_type',
            '',
        ],
        ids=[
            'Documented Content-Type',
            'Undocumented Content-Type',
            'Empty',
        ]
    )
    def test_content_types(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
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
    def test_missing_data(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
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
        [-1, '10', None],
        ids=['Negative', 'Wrong Type', 'None'],
    )
    def test_width_invalid(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
        width: Any
    ) -> None:
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

    @pytest.mark.parametrize(
        'width', [0, 0.1], ids=['Zero width', 'Float width']
    )
    def test_width_valid(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
        width: Any
    ) -> None:
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

    @pytest.mark.parametrize(
        'name', [
            'a',
            'a' * 64,
        ], ids=['Short name', 'Long name']
    )
    def test_name_valid(
        self,
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
        [1, '', 'a' * 65, None],
        ids=['Wrong Type', 'Empty', 'Too Long', 'None'],
    )
    def test_name_invalid(
        self,
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

    def test_existing_target_name(
        self,
        png_rgb: io.BytesIO,
        vuforia_server_credentials: VuforiaServerCredentials
    ) -> None:
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

    def test_image_valid(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        image_file: io.BytesIO,
    ) -> None:
        """
        JPEG and PNG files in the RGB and greyscale color spaces are
        allowed. The image must be under a threshold.

        This threshold is documented as being 2 MB but it is actually
        slightly larger. See the `png_large` fixture for more details.
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

    def test_bad_image(
        self,
        bad_image_file: io.BytesIO,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        A `BAD_REQUEST` response is returned if an image which is not a JPEG
        or PNG file is given, or if the given image is not in the greyscale or
        RGB color space.
        """
        image_data = bad_image_file.read()
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

    def test_too_large(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_large: io.BytesIO,
    ) -> None:
        """
        An `ImageTooLarge` result is returned if the image is above a certain
        threshold.

        This threshold is documented as being 2 MB but it is actually
        slightly larger. See the `png_large` fixture for more details.
        """
        original_data = png_large.getvalue()
        longer_data = original_data.replace(b'IEND', b'\x00' + b'IEND')
        too_large_file = io.BytesIO(longer_data)

        image_data = too_large_file.read()
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
            result_code=ResultCodes.IMAGE_TOO_LARGE,
        )

    def test_not_base64_encoded(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        If the given image is not decodable as base64 data then a `Fail`
        result is returned.
        """
        not_base64_encoded = b'a'

        with pytest.raises(binascii.Error):
            base64.b64decode(not_base64_encoded)

        data = {
            'name': 'example_name',
            'width': 1,
            'image': str(not_base64_encoded),
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.FAIL,
        )

    def test_not_image(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        If the given image is not an image file then a `BadImage` result is
        returned.
        """
        not_image_data = b'not_image_data'
        image_data_encoded = base64.b64encode(not_image_data).decode('ascii')

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

    @pytest.mark.parametrize('invalid_type_image', [1, None])
    def test_invalid_type(
        self,
        invalid_type_image: Any,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        If the given image is NULL, a `Fail` result is returned.
        """
        data = {
            'name': 'example_name',
            'width': 1,
            'image': invalid_type_image,
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


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestActiveFlag:
    """
    Tests for the active flag parameter.
    """

    @pytest.mark.parametrize('active_flag', [True, False, None])
    def test_valid(
        self,
        active_flag: Union[bool, None],
        png_rgb: io.BytesIO,
        vuforia_server_credentials: VuforiaServerCredentials
    ) -> None:
        """
        Boolean values and NULL are valid active flags.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')
        content_type = 'application/json'

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
            'active_flag': active_flag,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type=content_type,
        )

        assert_success(response=response)

    def test_invalid(
        self,
        png_rgb: io.BytesIO,
        vuforia_server_credentials: VuforiaServerCredentials
    ) -> None:
        """
        Values which are not Boolean values or NULL are not valid active flags.
        """
        active_flag = 'string'
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')
        content_type = 'application/json'

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
            'active_flag': active_flag,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
            content_type=content_type,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUnexpectedData:
    """
    Tests for passing data which is not mandatory or allowed to the endpoint.
    """

    def test_invalid_extra_data(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
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


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestApplicationMetadata:
    """
    Tests for the application metadata parameter.
    """

    def test_base64_encoded(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        A base64 encoded string is valid application metadata.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        metadata = b'Some data'
        metadata_encoded = base64.b64encode(metadata).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': metadata_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_success(response=response)

    def test_null(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        NULL is valid application metadata.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': None,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_success(response=response)

    def test_invalid_type(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        Values which are not a string or NULL are not valid application
        metadata.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': 1,
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

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_not_base64_encoded(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        A string which is not base64 encoded is not valid application metadata.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        not_base64_encoded = b'a'

        with pytest.raises(binascii.Error):
            base64.b64decode(not_base64_encoded)

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': str(not_base64_encoded),
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.FAIL,
        )
