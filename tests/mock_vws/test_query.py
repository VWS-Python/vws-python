"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import copy
import io
import uuid
from urllib.parse import urljoin

import requests
from requests import codes
from requests_mock import POST
from requests_toolbelt import MultipartEncoder

from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    authorization_header,
    rfc_1123_date,
)


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
        date = rfc_1123_date()
        request_path = '/v1/query'
        url = urljoin('https://cloudreco.vuforia.com', request_path)
        files = {'image': ('image.jpeg', image_content, 'image/jpeg')}

        # See https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html
        boundary = uuid.uuid4().hex

        multipart_encoded_data = MultipartEncoder(
            fields=files,
            boundary=boundary,
        )

        # We copy the encoded data because `to_string` mutates the object.
        content = copy.deepcopy(multipart_encoded_data).to_string()

        authorization_string = authorization_header(
            access_key=vuforia_database_keys.client_access_key,
            secret_key=vuforia_database_keys.client_secret_key,
            method=POST,
            content=content,
            # Note that this is not the actual Content-Type header value sent.
            content_type='multipart/form-data',
            date=date,
            request_path=request_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': f'multipart/form-data; boundary={boundary}',
        }

        request = requests.Request(
            method=POST,
            url=url,
            headers=headers,
            data=multipart_encoded_data,
        )

        prepared_request = request.prepare()
        session = requests.Session()
        response = session.send(request=prepared_request)  # type: ignore

        assert response.status_code == codes.OK
        assert response.json().keys() == {'result_code', 'results', 'query_id'}
        assert response.json()['result_code'] == 'Success'
        assert response.json()['results'] == []
