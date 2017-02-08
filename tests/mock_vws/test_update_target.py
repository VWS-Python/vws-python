"""
Tests for the mock of the update target endpoint.
"""

import base64
import binascii
import io
import json
from typing import Any, Dict, Union
from urllib.parse import urljoin

import pytest
import requests
from requests import Response, codes
from requests_mock import PUT

from common.constants import ResultCodes, TargetStatuses
from tests.mock_vws.utils import (
    add_target_to_vws,
    assert_vws_failure,
    assert_vws_response,
    get_vws_target,
    wait_for_target_processed,
)
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


def update_target(
    vuforia_server_credentials: VuforiaServerCredentials,
    data: Dict[str, Any],
    target_id: str,
    content_type: str='application/json',
) -> Response:
    """
    Helper to make a request to the endpoint to update a target.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        data: The data to send, in JSON format, to the endpoint.
        content_type: The `Content-Type` header to use.

    Returns:
        The response returned by the API.
    """
    date = rfc_1123_date()
    request_path = '/targets/' + target_id

    content = bytes(json.dumps(data), encoding='utf-8')

    authorization_string = authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=PUT,
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
        method=PUT,
        url=urljoin('https://vws.vuforia.com/', request_path),
        headers=headers,
        data=content,
    )

    return response


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUpdate:
    """
    Tests for updating targets.
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
        The `Content-Type` header does not change the response.
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
        )

        target_id = response.json()['target_id']

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'name': 'Adam'},
            target_id=target_id,
            content_type=content_type
        )

        # Code is FORBIDDEN because the target is processing
        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_STATUS_NOT_SUCCESS,
        )

    def test_no_fields_given(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        No data fields are required.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        assert response.json().keys() == {'result_code', 'transaction_id'}

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        # Targets go back to processing after
        assert response.json()['status'] == TargetStatuses.PROCESSING.value

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        assert response.json()['status'] == TargetStatuses.SUCCESS.value


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUnexpectedData:
    """
    Tests for passing data which is not allowed to the endpoint.
    """

    def test_invalid_extra_data(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        A `BAD_REQUEST` response is returned when unexpected data is given.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'extra_thing': 1},
            target_id=target_id,
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
        width: Any,
        target_id: str,
    ) -> None:
        """
        The width must be a non-negative number.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        original_width = response.json()['target_record']['width']

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'width': width},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        new_width = response.json()['target_record']['width']

        assert new_width == original_width

    @pytest.mark.parametrize(
        'width', [0, 0.1], ids=['Zero width', 'Float width']
    )
    def test_width_valid(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        width: Any,
        target_id: str,
    ) -> None:
        """
        Non-negative numbers are valid widths.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'width': width},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        new_width = response.json()['target_record']['width']
        assert new_width == width


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestActiveFlag:
    """
    Tests for the active flag parameter.
    """

    @pytest.mark.parametrize('initial_active_flag', [True, False])
    @pytest.mark.parametrize('desired_active_flag', [True, False])
    def test_active_flag(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb_success: io.BytesIO,
        initial_active_flag: bool,
        desired_active_flag: bool,
    ) -> None:
        """
        Setting the active flag to a Boolean value changes it.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
            'active_flag': initial_active_flag,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'active_flag': desired_active_flag},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        new_flag = response.json()['target_record']['active_flag']
        assert new_flag == desired_active_flag

    @pytest.mark.parametrize('desired_active_flag', ['string', None])
    def test_invalid(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
        desired_active_flag: Union[str, None],
    ) -> None:
        """
        Values which are not Boolean values are not valid active flags.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'active_flag': desired_active_flag},
            target_id=target_id,
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
        target_id: str,
    ) -> None:
        """
        A base64 encoded string is valid application metadata.
        """
        metadata = b'Some data'
        metadata_encoded = base64.b64encode(metadata).decode('ascii')

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'application_metadata': metadata_encoded},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

    @pytest.mark.parametrize('invalid_metadata', [1, None])
    def test_invalid_type(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
        invalid_metadata: Union[int, None],
    ) -> None:
        """
        Non-string values cannot be given as valid application metadata.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'application_metadata': invalid_metadata},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_not_base64_encoded(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        A string which is not base64 encoded is not valid application metadata.
        """
        not_base64_encoded = b'a'

        with pytest.raises(binascii.Error):
            base64.b64decode(not_base64_encoded)

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'application_metadata': str(not_base64_encoded)},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.FAIL,
        )


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
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        Names between 1 and 64 characters in length are valid.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'name': name},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        assert response.json()['target_record']['name'] == name

    @pytest.mark.parametrize(
        'name',
        [1, '', 'a' * 65, None],
        ids=['Wrong Type', 'Empty', 'Too Long', 'None'],
    )
    def test_name_invalid(
        self,
        name: str,
        target_id: str,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        A target's name must be a string of length 0 < N < 65.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'name': name},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_existing_target_name(
        self,
        png_rgb_success: io.BytesIO,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        Only one target can have a given name.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        first_target_name = 'example_name'
        second_target_name = 'another_example_name'

        data = {
            'name': first_target_name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        first_target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=first_target_id,
        )

        other_data = {
            'name': second_target_name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=other_data,
        )

        second_target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=second_target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'name': first_target_name},
            target_id=second_target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_NAME_EXIST,
        )

    def test_same_name_given(
        self,
        png_rgb_success: io.BytesIO,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        Updating a target with its own name does not give an error.
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        name = 'example'

        data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'name': name},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

        response = get_vws_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        assert response.json()['target_record']['name'] == name


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
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
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
        vuforia_server_credentials: VuforiaServerCredentials,
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
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
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
        vuforia_server_credentials: VuforiaServerCredentials,
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
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
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
        vuforia_server_credentials: VuforiaServerCredentials,
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
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
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
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ) -> None:
        """
        If the given image is not an image file then a `BadImage` result is
        returned.
        """
        not_image_data = b'not_image_data'
        image_data_encoded = base64.b64encode(not_image_data).decode('ascii')

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
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
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        If the given image is not a string, a `Fail` result is returned.
        """
        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={'image': invalid_type_image},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )
