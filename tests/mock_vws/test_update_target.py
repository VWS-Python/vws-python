"""
Tests for the mock of the update target endpoint.
"""

import base64
import io
import json
from typing import Any, Dict
from urllib.parse import urljoin

import pytest
import requests
from requests import Response, codes
from requests_mock import PUT

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    assert_vws_response,
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
        assert_vws_response(
            response=response,
            status_code=codes.FORBIDDEN,
            result_code=ResultCodes.TARGET_STATUS_NOT_SUCCESS,
        )

    def test_updating_multiple_fields(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
        png_rgb_success: io.BytesIO,
        content_type: str,
    ) -> None:
        """
        XXX
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

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = update_target(
            vuforia_server_credentials=vuforia_server_credentials,
            data={
                'name': 'changed',
                'width': 2,
                'image': png_rgb_success,
                'active_flag': False,
                # TODO: There's no way to test this...
                # TODO: Set this as new metadata string
                'application_metadata': ''

            },
            target_id=target_id,
            content_type=content_type
        )

    def test_no_fields_given(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
        content_type: str,
    ) -> None:
        pass


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestWidth:
    pass


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestTargetName:
    pass


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestActiveFlag:
    pass


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUnexpectedData:
    pass


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestApplicationMetadata:
    pass


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestImage:
    pass
