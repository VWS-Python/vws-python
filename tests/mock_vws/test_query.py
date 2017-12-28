"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import io
import uuid
from typing import Any, Dict
from urllib.parse import urljoin

import pytest
import requests
from requests import codes
from requests_mock import POST
from urllib3.filepost import encode_multipart_formdata

from tests.utils import VuforiaDatabaseKeys
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestQuery:
    """
    Tests for the query endpoint.
    """

    def test_no_results(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        With no results
        """
        image_content = high_quality_image.read()
        content_type = 'multipart/form-data'
        query: Dict[str, Any] = {}
        date = rfc_1123_date()
        request_path = '/v1/query'
        url = urljoin('https://cloudreco.vuforia.com', request_path)
        files = {'image': ('image.jpeg', image_content, 'image/jpeg')}

        request = requests.Request(
            method=POST,
            url=url,
            headers={},
            data=query,
            files=files,
        )

        prepared_request = request.prepare()  # type: ignore

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.client_access_key,
            secret_key=vuforia_database_keys.client_secret_key,
            method=POST,
            content=prepared_request.body,
            content_type=content_type,
            date=date,
            request_path=request_path,
        )

        headers = {
            **prepared_request.headers,
            'Authorization': authorization_string,
            'Date': date,
        }

        prepared_request.prepare_headers(headers=headers)
        p1 = prepared_request

        session = requests.Session()
        # response = session.send(request=prepared_request)  # type: ignore
        # assert response.status_code == codes.OK
        # assert response.json()['result_code'] == 'Success'
        # assert response.json()['results'] == []
        # assert 'query_id' in response.json()

        p1_boundary = uuid.uuid4().hex

        encoded_formdata = encode_multipart_formdata(
            files,
            boundary=p1_boundary,
        )

        content_2 = encoded_formdata[0]
        content_type_2 = encoded_formdata[1]

        authorization_string_2 = authorization_header(
            access_key=vuforia_database_keys.client_access_key,
            secret_key=vuforia_database_keys.client_secret_key,
            method=POST,
            content=content_2,
            content_type=content_type,
            date=date,
            request_path=request_path,
        )

        headers = {
            'Authorization': authorization_string_2,
            'Date': date,
            'Content-Type': content_type_2,
        }

        from requests_toolbelt import MultipartEncoder

        m = MultipartEncoder(
            fields=files,
            boundary=p1_boundary,
        )

        request_3 = requests.Request(
            method=POST,
            url=url,
            headers=headers,
            data=m,
        )

        p3 = request_3.prepare()
        resp3 = session.send(request=p3)  # type: ignore

        assert resp3.status_code == codes.OK
