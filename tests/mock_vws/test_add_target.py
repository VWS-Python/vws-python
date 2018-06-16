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

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    delete_target,
    wait_for_target_processed,
)
from tests.mock_vws.utils.assertions import (
    assert_vws_failure,
    assert_vws_response,
)
from tests.mock_vws.utils.authorization import VuforiaDatabaseKeys


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
        ],
    )
    def test_content_types(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
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
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
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
        [-1, '10', None, 0],
        ids=['Negative', 'Wrong Type', 'None', 'Zero'],
    )
    def test_width_invalid(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
        width: Any,
    ) -> None:
        """
        The width must be a number greater than zero.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': width,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_width_valid(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        Positive numbers are valid widths.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 0.01,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
            content_type='application/json',
        )

        assert_success(response=response)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestTargetName:
    """
    Tests for the target name field.
    """

    _MAX_CHAR_VALUE = 65535
    _MAX_NAME_LENGTH = 64

    @pytest.mark.parametrize(
        'name',
        [
            'á',
            # We test just below the max character value.
            # This is because targets with the max character value in their
            # names get stuck in the processing stage.
            chr(_MAX_CHAR_VALUE - 2),
            'a' * _MAX_NAME_LENGTH,
        ],
        ids=['Short name', 'Max char value', 'Long name'],
    )
    def test_name_valid(
        self,
        name: str,
        png_rgb: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
            content_type='application/json',
        )

        assert_success(response=response)

    @pytest.mark.parametrize(
        'name,status_code',
        [
            (1, codes.BAD_REQUEST),
            ('', codes.BAD_REQUEST),
            ('a' * (_MAX_NAME_LENGTH + 1), codes.BAD_REQUEST),
            (None, codes.BAD_REQUEST),
            (chr(_MAX_CHAR_VALUE + 1), codes.INTERNAL_SERVER_ERROR),
            (
                chr(_MAX_CHAR_VALUE + 1) * (_MAX_NAME_LENGTH + 1),
                codes.BAD_REQUEST,
            ),
        ],
        ids=[
            'Wrong Type',
            'Empty',
            'Too Long',
            'None',
            'Bad char',
            'Bad char too long',
        ],
    )
    def test_name_invalid(
        self,
        name: str,
        png_rgb: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        status_code: int,
    ) -> None:
        """
        A target's name must be a string of length 0 < N < 65, with characters
        in a particular range.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=status_code,
            result_code=ResultCodes.FAIL,
        )

    def test_existing_target_name(
        self,
        png_rgb: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_NAME_EXIST,
        )

    def test_deleted_existing_target_name(
        self,
        png_rgb: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        A target can be added with the name of a deleted target.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        delete_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_success(response=response)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestImage:
    """
    Tests for the image parameter.

    The specification for images is documented in "Supported Images" on
    https://library.vuforia.com/articles/Training/Image-Target-Guide
    """

    def test_image_valid(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
            content_type='application/json',
        )

        assert_success(response=response)

    def test_bad_image(
        self,
        bad_image_file: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.BAD_IMAGE,
        )

    def test_too_large(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.IMAGE_TOO_LARGE,
        )

    def test_not_base64_encoded(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.FAIL,
        )

    def test_not_image(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
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
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If the given image is not a string, a `Fail` result is returned.
        """
        data = {
            'name': 'example_name',
            'width': 1,
            'image': invalid_type_image,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
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
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
            content_type=content_type,
        )

        assert_success(response=response)

    def test_invalid(
        self,
        png_rgb: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
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
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
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

    _MAX_METADATA_BYTES = 1024 * 1024 - 1

    @pytest.mark.parametrize(
        'metadata',
        [
            b'a',
            b'a' * _MAX_METADATA_BYTES,
        ],
        ids=['Short', 'Max length'],
    )
    def test_base64_encoded(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
        metadata: bytes,
    ) -> None:
        """
        A base64 encoded string is valid application metadata.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')
        metadata_encoded = base64.b64encode(metadata).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': metadata_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_success(response=response)

    def test_null(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_success(response=response)

    def test_invalid_type(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
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
        vuforia_database_keys: VuforiaDatabaseKeys,
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
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.FAIL,
        )

    def test_metadata_too_large(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        A base64 encoded string of greater than 1024 * 1024 bytes is too large
        for application metadata.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')
        metadata = b'a' * (self._MAX_METADATA_BYTES + 1)
        metadata_encoded = base64.b64encode(metadata).decode('ascii')

        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': metadata_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.METADATA_TOO_LARGE,
        )


@pytest.mark.usefixtures('verify_mock_vuforia_inactive')
class TestInactiveProject:
    """
    Tests for inactive projects.
    """

    def test_inactive_project(
        self,
        inactive_database_keys: VuforiaDatabaseKeys,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        If the project is inactive, a FORBIDDEN response is returned.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_database_keys=inactive_database_keys,
            data=data,
            content_type='application/json',
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.PROJECT_INACTIVE,
        )
