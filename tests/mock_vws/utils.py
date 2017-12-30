"""
Utilities for tests for the VWS mock.
"""

import base64
import datetime
import email.utils
import hashlib
import hmac
import json
from string import hexdigits
from time import sleep
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
import timeout_decorator
from requests import Response
from requests_mock import GET, POST

from mock_vws._constants import ResultCodes, TargetStatuses


class VuforiaDatabaseKeys:
    """
    Credentials for VWS APIs.
    """

    def __init__(
        self,
        server_access_key: str,
        server_secret_key: str,
        client_access_key: str,
        client_secret_key: str,
        database_name: str,
    ) -> None:
        """
        Args:
            database_name: The name of a VWS target manager database name.
            server_access_key: A VWS server access key.
            server_secret_key: A VWS server secret key.
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.

        Attributes:
            database_name (str): The name of a VWS target manager database
                name.
            server_access_key (bytes): A VWS server access key.
            server_secret_key (bytes): A VWS server secret key.
            client_access_key (bytes): A VWS client access key.
            client_secret_key (bytes): A VWS client secret key.
        """
        self.server_access_key: bytes = bytes(
            server_access_key,
            encoding='utf-8',
        )
        self.server_secret_key: bytes = bytes(
            server_secret_key,
            encoding='utf-8',
        )
        self.client_access_key: bytes = bytes(
            client_access_key,
            encoding='utf-8',
        )
        self.client_secret_key: bytes = bytes(
            client_secret_key,
            encoding='utf-8',
        )
        self.database_name = database_name


class Endpoint:
    """
    Details of endpoints to be called in tests.
    """

    def __init__(
        self,
        example_path: str,
        method: str,
        successful_headers_result_code: ResultCodes,
        successful_headers_status_code: int,
        content_type: Optional[str],
        content: bytes,
    ) -> None:
        """
        Args:
            example_path: An example path for calling the endpoint.
            method: The HTTP method for the endpoint.
            successful_headers_result_code: The expected result code if the
                example path is requested with the method.
            successful_headers_status_code: The expected status code if the
                example path is requested with the method.
            content: The data to send with the request.
            content_type: The `Content-Type` header to send, and the content
                type to use to create the `Authorization` header.

        Attributes:
            example_path: An example path for calling the endpoint.
            method: The HTTP method for the endpoint.
            content_type: The `Content-Type` header to send, or `None` if one
                should not be sent.
            content: The data to send with the request.
            url: The URL to call the path with.
            successful_headers_result_code: The expected result code if the
                example path is requested with the method.
            successful_headers_status_code: The expected status code if the
                example path is requested with the method.
        """
        self.example_path = example_path
        self.method = method
        self.content_type = content_type
        self.content = content
        scheme = 'https://'
        host = 'vws.vuforia.com'
        base = scheme + host
        self.url = urljoin(base, example_path)
        self.successful_headers_status_code = successful_headers_status_code
        self.successful_headers_result_code = successful_headers_result_code
        self.host = host


def assert_vws_failure(
    response: Response,
    status_code: int,
    result_code: ResultCodes,
) -> None:
    """
    Assert that a VWS failure response is as expected.

    Args:
        response: The response returned by a request to VWS.
        status_code: The expected status code of the response.
        result_code: The expected result code of the response.

    Raises:
        AssertionError: The response is not in the expected VWS error format
            for the given codes.
    """
    assert response.json().keys() == {'transaction_id', 'result_code'}
    assert_vws_response(
        response=response,
        status_code=status_code,
        result_code=result_code,
    )


def assert_vws_response(
    response: Response,
    status_code: int,
    result_code: ResultCodes,
) -> None:
    """
    Assert that a VWS response is as expected, at least in part.

    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Interperete-VWS-API-Result-Codes
    implies that the expected status code can be worked out from the result
    code. However, this is not the case as the real results differ from the
    documentation.

    For example, it is possible to get a "Fail" result code and a 400 error.

    Args:
        response: The response returned by a request to VWS.
        status_code: The expected status code of the response.
        result_code: The expected result code of the response.

    Raises:
        AssertionError: The response is not in the expected VWS format for the
            given codes.
    """
    assert response.status_code == status_code
    response_result_code = response.json()['result_code']
    assert response_result_code == result_code.value
    response_header_keys = {
        'Connection',
        'Content-Length',
        'Content-Type',
        'Date',
        'Server',
    }
    assert response.headers.keys() == response_header_keys
    assert response.headers['Connection'] == 'keep-alive'
    assert response.headers['Content-Length'] == str(len(response.text))
    assert response.headers['Content-Type'] == 'application/json'
    assert response.headers['Server'] == 'nginx'
    transaction_id = response.json()['transaction_id']
    assert len(transaction_id) == 32
    assert all(char in hexdigits for char in transaction_id)
    date_response = response.headers['Date']
    date_from_response = email.utils.parsedate(date_response)
    assert date_from_response is not None
    year, month, day, hour, minute, second, _, _, _ = date_from_response
    datetime_from_response = datetime.datetime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
    )
    current_date = datetime.datetime.now()
    time_difference = abs(current_date - datetime_from_response)
    assert time_difference < datetime.timedelta(minutes=1)


def add_target_to_vws(
    vuforia_database_keys: VuforiaDatabaseKeys,
    data: Dict[str, Any],
    content_type: str = 'application/json',
) -> Response:
    """
    Return a response from a request to the endpoint to add a target.

    Args:
        vuforia_database_keys: The credentials to use to connect to Vuforia.
        data: The data to send, in JSON format, to the endpoint.
        content_type: The `Content-Type` header to use.

    Returns:
        The response returned by the API.
    """
    date = rfc_1123_date()
    request_path = '/targets'

    content = bytes(json.dumps(data), encoding='utf-8')

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
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
        url=urljoin('https://vws.vuforia.com/', request_path),
        headers=headers,
        data=content,
    )

    return response


def get_vws_target(
    target_id: str, vuforia_database_keys: VuforiaDatabaseKeys
) -> Response:
    """
    Return a response from a request to the endpoint to get a target record.

    Args:
        vuforia_database_keys: The credentials to use to connect to Vuforia.
        target_id: The ID of the target to return a record for.

    Returns:
        The response returned by the API.
    """
    response = target_api_request(
        server_access_key=vuforia_database_keys.server_access_key,
        server_secret_key=vuforia_database_keys.server_secret_key,
        method=GET,
        content=b'',
        request_path='/targets/' + target_id,
    )  # type: Response
    return response


def database_summary(vuforia_database_keys: VuforiaDatabaseKeys) -> Response:
    """
    Return the response of a request to the database summary endpoint.

    Args:
        vuforia_database_keys: The credentials to use to connect to Vuforia.

    Returns:
        The response of a request to the database summary endpoint.
    """
    response = target_api_request(
        server_access_key=vuforia_database_keys.server_access_key,
        server_secret_key=vuforia_database_keys.server_secret_key,
        method=GET,
        content=b'',
        request_path='/summary',
    )  # type: Response
    return response


@timeout_decorator.timeout(seconds=120)
def wait_for_target_processed(
    vuforia_database_keys: VuforiaDatabaseKeys,
    target_id: str,
) -> None:
    """
    Wait up to two minutes (arbitrary) for a target to get past the processing
    stage.

    Args:
        vuforia_database_keys: The credentials to use to connect to Vuforia.
        target_id: The ID of the target to wait for.

    Raises:
        TimeoutError: The target remained in the processing stage for more
            than two minutes.
    """
    while True:
        response = get_vws_target(
            target_id=target_id,
            vuforia_database_keys=vuforia_database_keys,
        )

        if response.json()['status'] != TargetStatuses.PROCESSING.value:
            return

        # We wait 0.2 seconds rather than less than that to decrease the number
        # of calls made to the API, to decrease the likelihood of hitting the
        # request quota.
        sleep(0.2)


def compute_hmac_base64(key: bytes, data: bytes) -> bytes:
    """
    Return the Base64 encoded HMAC-SHA1 hash of the given `data` using the
    provided `key`.
    """
    hashed = hmac.new(key=key, msg=None, digestmod=hashlib.sha1)
    hashed.update(msg=data)
    return base64.b64encode(s=hashed.digest())


def rfc_1123_date() -> str:
    """
    Return the date formatted as per RFC 2616, section 3.3.1, rfc1123-date, as
    described in
    https://library.vuforia.com/articles/Training/Using-the-VWS-API.
    """
    return email.utils.formatdate(None, localtime=False, usegmt=True)


def authorization_header(  # pylint: disable=too-many-arguments
    access_key: bytes,
    secret_key: bytes,
    method: str,
    content: bytes,
    content_type: str,
    date: str,
    request_path: str
) -> bytes:
    """
    Return an `Authorization` header which can be used for a request made to
    the VWS API with the given attributes.

    See https://library.vuforia.com/articles/Training/Using-the-VWS-API.

    Args:
        access_key: A VWS server or client access key.
        secret_key: A VWS server or client secret key.
        method: The HTTP method which will be used in the request.
        content: The request body which will be used in the request.
        content_type: The `Content-Type` header which is expected by
            endpoint. This does not necessarily have to match the
            `Content-Type` sent in the headers. In particular, for the query
            API, this must be set to `multipart/form-data` but the header must
            include the boundary.
        date: The current date which must exactly match the date sent in the
            `Date` header.
        request_path: The path to the endpoint which will be used in the
            request.

	Returns:
		Return an `Authorization` header which can be used for a request made
		to the VWS API with the given attributes.
    """
    hashed = hashlib.md5()
    hashed.update(content)
    content_md5_hex = hashed.hexdigest()

    components_to_sign = [
        method,
        content_md5_hex,
        content_type,
        date,
        request_path,
    ]
    string_to_sign = '\n'.join(components_to_sign)
    signature = compute_hmac_base64(
        key=secret_key,
        data=bytes(
            string_to_sign,
            encoding='utf-8',
        ),
    )
    auth_header = b'VWS %s:%s' % (access_key, signature)
    return auth_header


def target_api_request(
    server_access_key: bytes,
    server_secret_key: bytes,
    method: str,
    content: bytes,
    request_path: str,
) -> requests.Response:
    """
    Make a request to the Vuforia Target API.

    This uses `requests` to make a request against https://vws.vuforia.com.
    The content type of the request will be `application/json`.

    Args:
        server_access_key: A VWS server access key.
        server_secret_key: A VWS server secret key.
        method: The HTTP method which will be used in the request.
        content: The request body which will be used in the request.
        request_path: The path to the endpoint which will be used in the
            request.

    Returns:
        The response to the request made by `requests`.
    """
    date = rfc_1123_date()
    content_type = 'application/json'

    signature_string = authorization_header(
        access_key=server_access_key,
        secret_key=server_secret_key,
        method=method,
        content=content,
        content_type=content_type,
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': signature_string,
        'Date': date,
        'Content-Type': content_type,
    }

    url = urljoin(base='https://vws.vuforia.com', url=request_path)

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        data=content,
    )

    return response
