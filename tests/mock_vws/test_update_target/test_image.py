"""
Tests for the image field of the mock of the update target endpoint.
"""

import base64
import binascii
import io
from typing import Union

import pytest
from requests import codes

from mock_vws._constants import ResultCodes, TargetStatuses
from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    add_target_to_vws,
    assert_vws_failure,
    assert_vws_response,
    get_vws_target,
    update_target,
    wait_for_target_processed,
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
        vuforia_database_keys: VuforiaDatabaseKeys,
        image_file: io.BytesIO,
        target_id: str,
    ) -> None:
        """
        JPEG and PNG files in the RGB and greyscale color spaces are
        allowed. The image must be under a threshold.

        This threshold is documented as being 2 MB but it is actually
        slightly larger. See the `png_large` fixture for more details.
        """
        image_data = image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'image': image_data_encoded},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

    def test_bad_image(
        self,
        bad_image_file: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        A `BAD_REQUEST` response is returned if an image which is not a JPEG
        or PNG file is given, or if the given image is not in the greyscale or
        RGB color space.
        """
        image_data = bad_image_file.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'image': image_data_encoded},
            target_id=target_id,
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
        target_id: str,
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

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'image': image_data_encoded},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.IMAGE_TOO_LARGE,
        )

    def test_not_base64_encoded(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        If the given image is not decodable as base64 data then a `Fail`
        result is returned.
        """
        not_base64_encoded = b'a'

        with pytest.raises(binascii.Error):
            base64.b64decode(not_base64_encoded)

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'image': str(not_base64_encoded)},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.FAIL,
        )

    def test_not_image(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        If the given image is not an image file then a `BadImage` result is
        returned.
        """
        not_image_data = b'not_image_data'
        image_data_encoded = base64.b64encode(not_image_data).decode('ascii')

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'image': image_data_encoded},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.BAD_IMAGE,
        )

    @pytest.mark.parametrize('invalid_type_image', [1, None])
    def test_invalid_type(
        self,
        invalid_type_image: Union[int, None],
        target_id: str,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If the given image is not a string, a `Fail` result is returned.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'image': invalid_type_image},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_rating_can_change(
        self,
        png_rgb_success: io.BytesIO,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If the target is updated with an image of different quality, the
        tracking rating can change.

        "quality" refers to Vuforia's internal rating system.
        The mock randomly assigns a quality and makes sure that the new quality
        is different to the old quality.
        """
        poor_image = png_rgb_success.read()
        poor_image_data_encoded = base64.b64encode(poor_image).decode('ascii')

        good_image = high_quality_image.read()
        good_image_data_encoded = base64.b64encode(good_image).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': poor_image_data_encoded,
        }

        add_response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=data,
        )

        target_id = add_response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        get_response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        assert get_response.json()['status'] == TargetStatuses.SUCCESS.value
        # Tracking rating is between 0 and 5 when status is 'success'
        original_target_record = get_response.json()['target_record']
        original_tracking_rating = original_target_record['tracking_rating']
        assert original_tracking_rating in range(6)

        update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'image': good_image_data_encoded},
            target_id=target_id,
        )

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        get_response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        assert get_response.json()['status'] == TargetStatuses.SUCCESS.value
        # Tracking rating is between 0 and 5 when status is 'success'
        new_target_record = get_response.json()['target_record']
        new_tracking_rating = new_target_record['tracking_rating']
        assert new_tracking_rating in range(6)

        assert original_tracking_rating != new_tracking_rating
