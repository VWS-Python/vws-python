"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import base64
import calendar
import io
import time
from typing import Dict, Union
from urllib.parse import urljoin

import pytest
import requests
from requests import codes
from requests_mock import POST
from urllib3.filepost import encode_multipart_formdata

from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    add_target_to_vws,
    assert_query_success,
    assert_vwq_failure,
    authorization_header,
    rfc_1123_date,
    wait_for_target_processed,
)

VWQ_HOST = 'https://cloudreco.vuforia.com'


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestContentType:
    """
    Tests for the Content-Type header.
    """

    @pytest.mark.parametrize(
        'content_type',
        [
            'text/html',
            '',
        ],
    )
    def test_incorrect_no_boundary(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        content_type: str,
    ) -> None:
        """
        If a Content-Type header which is not ``multipart/form-data``, an
        ``UNSUPPORTED_MEDIA_TYPE`` response is given.
        """
        image_content = high_quality_image.getvalue()
        date = rfc_1123_date()
        request_path = '/v1/query'
        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        content, _ = encode_multipart_formdata(body)
        method = POST

        access_key = vuforia_database_keys.client_access_key
        secret_key = vuforia_database_keys.client_secret_key
        authorization_string = authorization_header(
            access_key=access_key,
            secret_key=secret_key,
            method=method,
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
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        assert response.text == ''
        assert_vwq_failure(
            response=response,
            status_code=codes.UNSUPPORTED_MEDIA_TYPE,
            content_type=None,
        )

    def test_incorrect_with_boundary(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If a Content-Type header which is not ``multipart/form-data``, an
        ``UNSUPPORTED_MEDIA_TYPE`` response is given.
        """
        image_content = high_quality_image.getvalue()
        date = rfc_1123_date()
        request_path = '/v1/query'
        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        content, content_type_header = encode_multipart_formdata(body)
        method = POST

        content_type = 'text/html'

        access_key = vuforia_database_keys.client_access_key
        secret_key = vuforia_database_keys.client_secret_key
        authorization_string = authorization_header(
            access_key=access_key,
            secret_key=secret_key,
            method=method,
            content=content,
            content_type=content_type,
            date=date,
            request_path=request_path,
        )

        _, boundary = content_type_header.split(';')

        content_type = 'text/html; ' + boundary
        headers = {
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': content_type,
        }

        response = requests.request(
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        assert response.text == ''
        assert_vwq_failure(
            response=response,
            status_code=codes.UNSUPPORTED_MEDIA_TYPE,
            content_type=None,
        )

    @pytest.mark.parametrize(
        'content_type',
        [
            'multipart/form-data',
            'multipart/form-data; extra',
            'multipart/form-data; extra=1',
        ],
    )
    def test_no_boundary(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        content_type: str,
    ) -> None:
        """
        If no boundary is given, a ``BAD_REQUEST`` is returned.
        """
        image_content = high_quality_image.getvalue()
        date = rfc_1123_date()
        request_path = '/v1/query'
        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        content, _ = encode_multipart_formdata(body)
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
            'Content-Type': content_type,
        }

        response = requests.request(
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        expected_text = (
            'java.io.IOException: RESTEASY007550: '
            'Unable to get boundary for multipart'
        )
        assert response.text == expected_text
        assert_vwq_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            content_type='text/html',
        )

    def test_bogus_boundary(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If a bogus boundary is given, a ``BAD_REQUEST`` is returned.
        """
        image_content = high_quality_image.getvalue()
        date = rfc_1123_date()
        request_path = '/v1/query'
        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        content, _ = encode_multipart_formdata(body)
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
            'Content-Type': 'multipart/form-data; boundary=example_boundary',
        }

        response = requests.request(
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        expected_text = (
            'java.lang.RuntimeException: RESTEASY007500: '
            'Could find no Content-Disposition header within part'
        )
        assert response.text == expected_text
        assert_vwq_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            content_type='text/html',
        )

    def test_extra_section(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If a bogus boundary is given, a ``BAD_REQUEST`` is returned.
        """
        image_content = high_quality_image.getvalue()
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
            'Content-Type': content_type_header + '; extra=1',
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
class TestSuccess:
    """
    Tests for successful calls to the query endpoint.
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
        image_content = high_quality_image.getvalue()
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

    def test_match(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If the exact image that was added is queried for, target data is shown.
        """
        image_content = high_quality_image.getvalue()
        image_data_encoded = base64.b64encode(image_content).decode('ascii')
        name = 'example_name'
        add_target_data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
        }
        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=add_target_data,
        )

        target_id = response.json()['target_id']
        approximate_target_created = calendar.timegm(time.gmtime())

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )
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
        [result] = response.json()['results']
        assert result.keys() == {'target_id', 'target_data'}
        assert result['target_id'] == target_id
        target_data = result['target_data']
        assert target_data.keys() == {
            'application_metadata',
            'name',
            'target_timestamp',
        }
        assert target_data['application_metadata'] is None
        assert target_data['name'] == name
        target_timestamp = target_data['target_timestamp']
        assert isinstance(target_timestamp, int)
        time_difference = abs(approximate_target_created - target_timestamp)
        assert time_difference < 5


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestMaxNumResults:
    """
    Tests for the ``max_num_results`` parameter.
    """

    def test_default(self) -> None:
        """
        The default ``max_num_results`` is 1.

        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """

    @pytest.mark.parametrize('num_results', [1, b'1', 50])
    def test_valid(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        num_results: Union[int, bytes],
    ) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.

        We assert that the response is a success, but not that the maximum
        number of results is enforced.

        The documentation at
        https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.  # noqa: E501
        states that this must be between 1 and 10, but in practice, 50 is the
        maximum.
        """
        image_content = high_quality_image.getvalue()
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

    @pytest.mark.parametrize('num_results', [-1, 0, 51])
    def test_out_of_range(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        num_results: Union[int, bytes],
    ) -> None:
        """
        An error is returned if ``max_num_results`` is given as an integer out
        of the range (1, 50).

        The documentation at
        https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.  # noqa: E501
        states that this must be between 1 and 10, but in practice, 50 is the
        maximum.
        """
        image_content = high_quality_image.getvalue()
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

        expected_text = (
            f'Integer out of range ({num_results}) in form data part '
            "'max_result'. Accepted range is from 1 to 50 (inclusive)."
        )
        assert response.text == expected_text
        assert_vwq_failure(
            response=response,
            content_type='application/json',
            status_code=codes.BAD_REQUEST,
        )

    @pytest.mark.parametrize(
        'num_results',
        [b'0.1', b'1.1', b'a', b'2147483648'],
    )
    def test_invalid_type(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        num_results: bytes,
    ) -> None:
        """
        An error is returned if ``max_num_results`` is given as something other
        than an integer.

        Integers greater than 2147483647 are not considered integers because
        they are bigger than Java's maximum integer.
        """
        image_content = high_quality_image.getvalue()
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

        expected_text = (
            f"Invalid value '{num_results.decode()}' in form data part "
            "'max_result'. "
            'Expecting integer value in range from 1 to 50 (inclusive).'
        )
        assert response.text == expected_text
        assert_vwq_failure(
            response=response,
            content_type='application/json',
            status_code=codes.BAD_REQUEST,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestIncludeTargetData:
    """
    Tests for the ``include_target_data`` parameter.
    """

    def test_default(self) -> None:
        """
        The default ``include_target_data`` is 'top'.

        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """

    @pytest.mark.parametrize('include_target_data', ['top', 'none', 'all'])
    def test_valid(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        include_target_data: str,
    ) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.

        We assert that the response is a success, but not that the preference
        is enforced.
        """
        image_content = high_quality_image.getvalue()
        date = rfc_1123_date()
        request_path = '/v1/query'
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'include_target_data': (None, include_target_data, 'text/plain'),
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

    def test_invalid_value(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        A ``BAD_REQUEST`` error is given when a string that is not one of
        'none', 'top' or 'all'.
        """
        image_content = high_quality_image.getvalue()
        date = rfc_1123_date()
        request_path = '/v1/query'
        include_target_data = 'a'
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'include_target_data': (None, include_target_data, 'text/plain'),
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

        expected_text = (
            f"Invalid value '{include_target_data}' in form data part "
            "'include_target_data'. "
            "Expecting one of the (unquoted) string values 'all', 'none' or "
            "'top'."
        )
        assert response.text == expected_text
        assert_vwq_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            content_type='application/json',
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestAcceptHeader:
    """
    Tests for the ``Accept`` header.
    """

    @pytest.mark.parametrize(
        'extra_headers',
        [
            {
                'Accept': 'application/json',
            },
            {},
        ],
    )
    def test_valid(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        extra_headers: Dict[str, str],
    ) -> None:
        """
        An ``Accept`` header can be given iff its value is "application/json".
        """
        image_content = high_quality_image.getvalue()
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
            **extra_headers,
        }

        response = requests.request(
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        assert_query_success(response=response)
        assert response.json()['results'] == []

    def test_invalid(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        A NOT_ACCEPTABLE response is returned if an ``Accept`` header is given
        with a value which is not "application/json".
        """
        image_content = high_quality_image.getvalue()
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
            'Accept': 'text/html',
        }

        response = requests.request(
            method=method,
            url=urljoin(base=VWQ_HOST, url=request_path),
            headers=headers,
            data=content,
        )

        assert_vwq_failure(
            response=response,
            status_code=codes.NOT_ACCEPTABLE,
            content_type=None,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestActiveFlag:
    """
    Tests for active targets.
    """

    def test_inactive(self) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestMaximumImageSize:
    """
    Tests for maximum image sizes.
    """

    def test_png(self) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """

    def test_jpeg(self) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestImageFormats:
    """
    Tests for various image formats.
    """

    def test_supported(self) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """

    def test_unsupported(self) -> None:
        """
        See https://github.com/adamtheturtle/vws-python/issues/357 for
        implementing this test.
        """
