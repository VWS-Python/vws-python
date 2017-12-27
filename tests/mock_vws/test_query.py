"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import base64
import io
import json
from typing import Any, Dict
from urllib.parse import urljoin

import pytest
import requests
from requests_mock import POST

from tests.utils import VuforiaDatabaseKeys
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestQuery:
    """
    XXX
    """

    def test_no_results(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        XXX
        """
        image_data = high_quality_image.read()
        base64.b64encode(image_data).decode('ascii')

        date = rfc_1123_date()
        request_path = '/v1/query'
        content_type = 'multipart/form-data'

        data: Dict[str, Any] = {}

        files = {'image': ('image.jpeg', image_data, 'image/jpeg')}

        content = bytes(json.dumps(data), encoding='utf-8')

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.client_access_key,
            secret_key=vuforia_database_keys.client_secret_key,
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
