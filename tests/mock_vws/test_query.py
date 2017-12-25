"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import base64
import io
from typing import Any, Dict
from urllib.parse import urljoin

import pytest
import requests
from requests import Response, codes
from requests_mock import POST

from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date
import json

@pytest.mark.usefixtures('verify_mock_vuforia')
class TestQuery:
    """
    XXX
    """

    """
    * Normal query
    * Maximum size PNG
    * Bad content type
    * Maximum size JPG
    * max_num_results
    * include_target_data
    * Active flag
    * Success: False
    """

    def test_no_results(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        high_quality_image: io.BytesIO,
    ):
        """
        XXX
        """
        image_data = high_quality_image.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        date = rfc_1123_date()
        request_path = '/v1/query'
        content_type = 'multipart/form-data'

        data = {
            # 'image': image_data_encoded,
        }

        files={'image': ('image.jpeg', image_data, 'image/jpeg')}

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
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': content_type,
        }

        response = requests.request(
            method=POST,
            url=urljoin('https://cloudreco.vuforia.com', request_path),
            headers=headers,
            data=data,
            files=files,
        )

        assert 'results' not in response.json()
        assert response.status_code == 200
