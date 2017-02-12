"""
Utilities for tests for the VWS mock.
"""

import datetime
import email.utils
import json
from string import hexdigits
from time import sleep
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
import timeout_decorator
from requests import Response
from requests_mock import GET, POST

from common.constants import ResultCodes, TargetStatuses
from tests.utils import VuforiaServerCredentials
from vws._request_utils import (
    authorization_header,
    rfc_1123_date,
    target_api_request,
)


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
        self.url = urljoin('https://vws.vuforia.com/', example_path)
        self.successful_headers_status_code = successful_headers_status_code
        self.successful_headers_result_code = successful_headers_result_code


def assert_vws_failure(
    response: Response, status_code: int, result_code: ResultCodes
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

    https://library.vuforia.com/articles/Solution/How-To-Interperete-VWS-API-Result-Codes
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
    vuforia_server_credentials: VuforiaServerCredentials,
    data: Dict[str, Any],
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
    request_path = '/targets'

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
        "Authorization": authorization_string,
        "Date": date,
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
    target_id: str, vuforia_server_credentials: VuforiaServerCredentials
) -> Response:
    """
    Helper to make a request to the endpoint to get a target record.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        target_id: The ID of the target to return a record for.

    Returns:
        The response returned by the API.
    """
    return target_api_request(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        request_path='/targets/' + target_id,
    )


@timeout_decorator.timeout(seconds=60)
def wait_for_target_processed(
    vuforia_server_credentials: VuforiaServerCredentials,
    target_id: str,
) -> None:
    """
    Wait up to one minute (arbitrary) for a target to get past the processing
    stage.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        target_id: The ID of the target to wait for.

    Raises:
        TimeoutError: The target remained in the processing stage for more
            than 15 seconds.
    """
    while True:
        response = get_vws_target(
            target_id=target_id,
            vuforia_server_credentials=vuforia_server_credentials
        )

        if response.json()['status'] != TargetStatuses.PROCESSING.value:
            return

        # We wait 0.2 seconds rather than less than that to decrease the number
        # of calls made to the API, to decrease the likelihood of hitting the
        # request quota.
        sleep(0.2)
