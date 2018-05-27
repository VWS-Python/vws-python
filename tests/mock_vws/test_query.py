"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import base64
import calendar
import io
import time
from typing import Any, Dict, Union
from urllib.parse import urljoin

import pytest
import requests
from requests import Response, codes
from requests_mock import POST
from urllib3.filepost import encode_multipart_formdata

from mock_vws._constants import TargetStatuses
from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    add_target_to_vws,
    assert_query_success,
    assert_vwq_failure,
    authorization_header,
    get_vws_target,
    rfc_1123_date,
    update_target,
    wait_for_target_processed,
)

VWQ_HOST = 'https://cloudreco.vuforia.com'


def query(
    vuforia_database_keys: VuforiaDatabaseKeys,
    body: Dict[str, Any],
) -> Response:
    """
    Make a request to the endpoint to make an image recognition query.

    Args:
        vuforia_database_keys: The credentials to use to connect to
            Vuforia.
        body: The request body to send in ``multipart/formdata`` format.

    Returns:
        The response returned by the API.
    """
    date = rfc_1123_date()
    request_path = '/v1/query'
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

    return response


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
        If a Content-Type header which is not ``multipart/form-data`` is given
        with the correct boundary, an ``UNSUPPORTED_MEDIA_TYPE`` response is
        given.
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
        If sections that are not the boundary section are given in the header,
        that is fine.
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
        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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
        metadata_encoded = base64.b64encode(b'example').decode('ascii')
        name = 'example_name'
        add_target_data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': metadata_encoded,
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

        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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
        assert target_data['application_metadata'] == metadata_encoded
        assert target_data['name'] == name
        target_timestamp = target_data['target_timestamp']
        assert isinstance(target_timestamp, int)
        time_difference = abs(approximate_target_created - target_timestamp)
        assert time_difference < 5


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestIncorrectFields:
    """
    Tests for incorrect and unexpected fields.
    """

    def test_missing_image(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If an image is not given, a ``BAD_REQUEST`` response is returned.
        """
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body={},
        )

        assert response.text == 'No image.'
        assert_vwq_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            content_type='application/json',
        )

    def test_extra_fields(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If extra fields are given, a ``BAD_REQUEST`` response is returned.
        """
        image_content = high_quality_image.getvalue()
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'extra_field': (None, 1, 'text/plain'),
        }

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )

        assert response.text == 'Unknown parameters in the request.'
        assert_vwq_failure(
            response=response,
            content_type='application/json',
            status_code=codes.BAD_REQUEST,
        )

    def test_missing_image_and_extra_fields(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        If extra fields are given and no image field is given, a
        ``BAD_REQUEST`` response is returned.

        The extra field error takes precedence.
        """
        body = {
            'extra_field': (None, 1, 'text/plain'),
        }

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )

        assert response.text == 'Unknown parameters in the request.'
        assert_vwq_failure(
            response=response,
            content_type='application/json',
            status_code=codes.BAD_REQUEST,
        )


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
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'max_num_results': (None, num_results, 'text/plain'),
        }

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'max_num_results': (None, num_results, 'text/plain'),
        }

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'max_num_results': (None, num_results, 'text/plain'),
        }
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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
        """
        image_content = high_quality_image.getvalue()
        image_data_encoded = base64.b64encode(image_content).decode('ascii')
        for name in ('example_1', 'example_2'):
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

            wait_for_target_processed(
                target_id=target_id,
                vuforia_database_keys=vuforia_database_keys,
            )

        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'include_target_data': (None, include_target_data, 'text/plain'),
            'max_num_results': (None, 2, 'text/plain'),
        }

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )

        assert_query_success(response=response)
        result_1, result_2 = response.json()['results']
        assert 'target_data' in result_1
        assert 'target_data' not in result_2


    @pytest.mark.parametrize('include_target_data', ['top', 'TOP'])
    def test_top(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        include_target_data: str,
    ) -> None:
        """
        When ``include_target_data`` is set to "top" (case insensitive), only
        the first result includes target data.
        """
        image_content = high_quality_image.getvalue()
        image_data_encoded = base64.b64encode(image_content).decode('ascii')
        for name in ('example_1', 'example_2'):
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

            wait_for_target_processed(
                target_id=target_id,
                vuforia_database_keys=vuforia_database_keys,
            )

        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'include_target_data': (None, include_target_data, 'text/plain'),
            'max_num_results': (None, 2, 'text/plain'),
        }

        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )

        assert_query_success(response=response)
        result_1, result_2 = response.json()['results']
        assert 'target_data' in result_1
        assert 'target_data' not in result_2

    @pytest.mark.parametrize('include_target_data', ['none', 'NONE'])
    def test_none(
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
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'include_target_data': (None, include_target_data, 'text/plain'),
        }
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )

        assert_query_success(response=response)
        assert response.json()['results'] == []

    @pytest.mark.parametrize('include_target_data', ['all', 'ALL'])
    def test_all(
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
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'include_target_data': (None, include_target_data, 'text/plain'),
        }
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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
        'none', 'top' or 'all' (case insensitive).
        """
        image_content = high_quality_image.getvalue()
        include_target_data = 'a'
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'include_target_data': (None, include_target_data, 'text/plain'),
        }
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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

    def test_inactive(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        Images which are not active are not matched.
        """
        image_content = high_quality_image.getvalue()
        image_data_encoded = base64.b64encode(image_content).decode('ascii')
        name = 'example_name'
        add_target_data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
            'active_flag': False,
        }
        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=add_target_data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )

        assert_query_success(response=response)
        assert response.json()['results'] == []


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


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestProcessing:
    """
    Tests for targets in the processing state.
    """

    @pytest.mark.parametrize(
        'active_flag',
        [True, False],
    )
    def test_processing(
        self,
        high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
        active_flag: bool,
    ) -> None:
        """
        When a target with a matching image is in the processing state it is
        not matched.

        Sometimes an `INTERNAL_SERVER_ERROR` response is returned.
        """
        image_content = high_quality_image.getvalue()
        image_data_encoded = base64.b64encode(image_content).decode('ascii')
        name = 'example_name'
        add_target_data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
            'active_flag': active_flag,
        }
        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=add_target_data,
        )

        target_id = response.json()['target_id']

        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )

        # We assert that after making a query, the target is in th processing
        # state.
        #
        # There is a race condition here.
        #
        # This is really a check that the test is valid.
        #
        # If the target is no longer in the processing state here, it may be
        # that the test was valid, but the target went into the processed
        # state.
        #
        # If the target is no longer in the processing state here, that is a
        # flaky test that is the test's fault and this must be rethought.
        get_target_response = get_vws_target(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        # Targets go back to processing after being updated.
        target_status = get_target_response.json()['status']
        assert target_status == TargetStatuses.PROCESSING.value

        # Sometimes we get a 500 error, sometimes we do not.

        if response.status_code == codes.OK:  # pragma: no cover
            assert response.json()['results'] == []
            assert_query_success(response=response)
            return

        # We do not mark this with "pragma: no cover" because we choose to
        # implement the mock to have this behavior.
        # The response text for a 500 response is not consistent.
        # Therefore we only test for consistent features.
        assert 'Error 500 Server Error' in response.text
        assert 'HTTP ERROR 500' in response.text
        assert 'Problem accessing /v1/query' in response.text

        assert_vwq_failure(
            response=response,
            content_type='text/html; charset=ISO-8859-1',
            status_code=codes.INTERNAL_SERVER_ERROR,
        )


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestUpdate:
    """
    Tests for updated targets.
    """

    def test_updated_target(
        self,
        high_quality_image: io.BytesIO,
        different_high_quality_image: io.BytesIO,
        vuforia_database_keys: VuforiaDatabaseKeys,
    ) -> None:
        """
        After a target is updated, only the new image can be matched.
        The match result includes the updated name, timestamp and application
        metadata.
        """
        image_content = high_quality_image.getvalue()
        image_data_encoded = base64.b64encode(image_content).decode('ascii')
        metadata = b'example_metadata'
        metadata_encoded = base64.b64encode(metadata).decode('ascii')
        name = 'example_name'
        add_target_data = {
            'name': name,
            'width': 1,
            'image': image_data_encoded,
            'application_metadata': metadata_encoded,
        }
        response = add_target_to_vws(
            vuforia_database_keys=vuforia_database_keys,
            data=add_target_data,
        )

        target_id = response.json()['target_id']
        calendar.timegm(time.gmtime())

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        new_image_content = different_high_quality_image.getvalue()

        new_name = name + '2'
        new_metadata = metadata + b'2'
        new_image_data_encoded = base64.b64encode(new_image_content,
                                                  ).decode('ascii')
        new_metadata_encoded = base64.b64encode(new_metadata).decode('ascii')
        update_data = {
            'name': new_name,
            'image': new_image_data_encoded,
            'application_metadata': new_metadata_encoded,
        }

        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )
        [result] = response.json()['results']
        target_data = result['target_data']
        target_timestamp = target_data['target_timestamp']
        original_target_timestamp = int(target_timestamp)

        update_target(
            vuforia_database_keys=vuforia_database_keys,
            data=update_data,
            target_id=target_id,
        )

        approximate_target_updated = calendar.timegm(time.gmtime())

        wait_for_target_processed(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        body = {'image': ('image.jpeg', new_image_content, 'image/jpeg')}
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
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
        assert target_data['application_metadata'] == new_metadata_encoded
        assert target_data['name'] == new_name
        target_timestamp = target_data['target_timestamp']
        assert isinstance(target_timestamp, int)
        # In the future we might want to test that
        # target_timestamp > original_target_timestamp
        # However, this requires us to set the mock processing time at > 1
        # second.
        assert target_timestamp >= original_target_timestamp
        time_difference = abs(approximate_target_updated - target_timestamp)
        assert time_difference < 5

        body = {'image': ('image.jpeg', image_content, 'image/jpeg')}
        response = query(
            vuforia_database_keys=vuforia_database_keys,
            body=body,
        )
        assert_query_success(response=response)
        assert response.json()['results'] == []
