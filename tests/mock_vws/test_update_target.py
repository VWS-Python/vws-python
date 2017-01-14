"""
Tests for the mock of the update target endpoint.
"""

import base64
import binascii
import io
import json
from string import hexdigits
from typing import Any, Dict, Union
from urllib.parse import urljoin

import pytest
import requests
from requests import Response, codes
from requests_mock import POST, PUT

from common.constants import ResultCodes
from tests.mock_vws.utils import (
    add_target_to_vws,
    assert_vws_failure,
    assert_vws_response,
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
        )

        assert_success(response=response)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestName:
    """
    """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestWidth:
    """
    """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestImage:
    """
    """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestActiveFlag:
    """
    """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestApplicationMetadata:
    """
    Tests for the application metadata parameter.
    """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUnexpectedData:
    """
    Tests for passing data which is not mandatory or allowed to the endpoint.
    """
