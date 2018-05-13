"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import io
from urllib.parse import urljoin

import pytest
import requests
from requests_mock import POST
from urllib3.filepost import encode_multipart_formdata

from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    assert_query_success,
    authorization_header,
    rfc_1123_date,
)


VWQ_HOST = 'https://cloudreco.vuforia.com'


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestQuery:
    """
    Tests for the query endpoint.
    """

    def test_no_results(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        When there are no matching images in the database, an empty list of
        results is returned.
        """
        image_content = high_quality_image.read()
        date = rfc_1123_date()
        request_path = '/v1/query'
        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        content, content_type_header = encode_multipart_formdata(body)
        method = POST

        access_key = vuforia_database_keys.client_access_key
        secret_key = vuforia_database_keys.client_secret_key
        authorization_string = authorization_header(
            access_key=access_key,
            secret_key=secret_key,
            method=method,
            content=content,
            # Note that this is not the actual Content-Type header value sent.
            content_type='multipart/form-data',
            date=date,
            request_path=request_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': content_type_header,
        }

        response = requests.request(
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        assert_query_success(response=response)
        assert response.json()['results'] == []


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestMaxNumResults:
    """
    Tests for the ``max_num_results`` parameter.
    """

    def test_default(self):
        """
        The default ``max_num_results`` is 1.

        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """

    @pytest.mark.parametrize('num_results', [1, 50])
    def test_valid(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        num_results: int,
    ) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.

        We assert that the response is a success, but not that the maximum
        number of results is enforced.

        The documentation at
        https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.  # noqa: F401
        states that this must be between 1 and 10, but in practice, 50 is the
        maximum.
        """
        image_content = high_quality_image.read()
        date = rfc_1123_date()
        request_path = '/v1/query'
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'max_num_results': (None, num_results, 'text/plain'),
        }
        content, content_type_header = encode_multipart_formdata(body)
        method = POST

        access_key = vuforia_database_keys.client_access_key
        secret_key = vuforia_database_keys.client_secret_key
        authorization_string = authorization_header(
            access_key=access_key,
            secret_key=secret_key,
            method=method,
            content=content,
            # Note that this is not the actual Content-Type header value sent.
            content_type='multipart/form-data',
            date=date,
            request_path=request_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': content_type_header,
        }

        response = requests.request(
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        assert_query_success(response=response)
        assert response.json()['results'] == []

    # def test_invalid(self):
    #     """
    #     XXX
    #     """
    #     image_content = high_quality_image.read()
    #     date = rfc_1123_date()
    #     request_path = '/v1/query'
    #     body = {
    #         'image': ('image.jpeg', image_content, 'image/jpeg'),
    #         'max_num_results': ('image.jpeg', image_content, 'image/jpeg'),
    #     }
    #     content, content_type_header = encode_multipart_formdata(body)
    #     method = POST
    #
    #     access_key = vuforia_database_keys.client_access_key
    #     secret_key = vuforia_database_keys.client_secret_key
    #     authorization_string = authorization_header(
    #         access_key=access_key,
    #         secret_key=secret_key,
    #         method=method,
    #         content=content,
    #         # Note that this is not the actual Content-Type header value sent.
    #         content_type='multipart/form-data',
    #         date=date,
    #         request_path=request_path,
    #     )
    #
    #     headers = {
    #         'Authorization': authorization_string,
    #         'Date': date,
    #         'Content-Type': content_type_header,
    #     }
    #
    #     response = requests.request(
    #         method=method,
    #         url=urljoin(base=VWQ_HOST, url=request_path),
    #         headers=headers,
    #         data=content,
    #     )
    #
    #     assert_query_success(response=response)
    #     assert response.json()['results'] == []
