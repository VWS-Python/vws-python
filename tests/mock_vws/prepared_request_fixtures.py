"""
Configuration, plugins and fixtures for `pytest`.
"""

import json
from typing import Any, Dict
from urllib.parse import urljoin

import pytest
import requests
from requests import codes
from requests_mock import DELETE, GET, POST, PUT

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
    VuforiaDatabaseKeys,
    authorization_header,
    rfc_1123_date,
    wait_for_target_processed,
)

VWS_HOST = 'https://vws.vuforia.com'


@pytest.fixture()
def _add_target(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for adding a target.
    """
    date = rfc_1123_date()
    data: Dict[str, Any] = {}
    request_path = '/targets'
    content_type = 'application/json'
    method = POST

    content = bytes(json.dumps(data), encoding='utf-8')

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
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

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore

    return TargetAPIEndpoint(
        # We expect a bad request error because we have not given the required
        # JSON body elements.
        successful_headers_status_code=codes.BAD_REQUEST,
        successful_headers_result_code=ResultCodes.FAIL,
        prepared_request=prepared_request,
    )


@pytest.fixture()
def _delete_target(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
    target_id: str,  # pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for deleting a target.
    """
    wait_for_target_processed(
        vuforia_database_keys=vuforia_database_keys,
        target_id=target_id,
    )
    date = rfc_1123_date()
    request_path = f'/targets/{target_id}'
    method = DELETE
    content = b''

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
        method=method,
        content=content,
        content_type='',
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': authorization_string,
        'Date': date,
    }

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore
    return TargetAPIEndpoint(
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        prepared_request=prepared_request,
    )


@pytest.fixture()
def _database_summary(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for getting details about the database.
    """
    date = rfc_1123_date()
    request_path = '/summary'
    method = GET

    content = b''

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
        method=method,
        content=content,
        content_type='',
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': authorization_string,
        'Date': date,
    }

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore

    return TargetAPIEndpoint(
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        prepared_request=prepared_request,
    )


@pytest.fixture()
def _get_duplicates(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
    target_id: str,  # pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for getting potential duplicates of a
    target.
    """
    wait_for_target_processed(
        vuforia_database_keys=vuforia_database_keys,
        target_id=target_id,
    )
    date = rfc_1123_date()
    request_path = f'/duplicates/{target_id}'
    method = GET

    content = b''

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
        method=method,
        content=content,
        content_type='',
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': authorization_string,
        'Date': date,
    }

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore

    return TargetAPIEndpoint(
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        prepared_request=prepared_request,
    )


@pytest.fixture()
def _get_target(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
    target_id: str,  # pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for getting details of a target.
    """
    wait_for_target_processed(
        vuforia_database_keys=vuforia_database_keys,
        target_id=target_id,
    )
    date = rfc_1123_date()
    request_path = f'/targets/{target_id}'
    method = GET

    content = b''

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
        method=method,
        content=content,
        content_type='',
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': authorization_string,
        'Date': date,
    }

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore

    return TargetAPIEndpoint(
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        prepared_request=prepared_request,
    )


@pytest.fixture()
def _target_list(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for getting a list of targets.
    """
    date = rfc_1123_date()
    request_path = '/targets'
    method = GET

    content = b''

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
        method=method,
        content=content,
        content_type='',
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': authorization_string,
        'Date': date,
    }

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore

    return TargetAPIEndpoint(
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        prepared_request=prepared_request,
    )


@pytest.fixture()
def _target_summary(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
    target_id: str,  # pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for getting a summary report of a target.
    """
    wait_for_target_processed(
        vuforia_database_keys=vuforia_database_keys,
        target_id=target_id,
    )
    date = rfc_1123_date()
    request_path = f'/summary/{target_id}'
    method = GET

    content = b''

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
        method=method,
        content=content,
        content_type='',
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': authorization_string,
        'Date': date,
    }

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore

    return TargetAPIEndpoint(
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        prepared_request=prepared_request,
    )


@pytest.fixture()
def _update_target(
    vuforia_database_keys: VuforiaDatabaseKeys,  # noqa: E501 pylint: disable=redefined-outer-name
    target_id: str,  # pylint: disable=redefined-outer-name
) -> TargetAPIEndpoint:
    """
    Return details of the endpoint for updating a target.
    """
    wait_for_target_processed(
        vuforia_database_keys=vuforia_database_keys,
        target_id=target_id,
    )
    data: Dict[str, Any] = {}
    request_path = f'/targets/{target_id}'
    content = bytes(str(data), encoding='utf-8')
    content_type = 'application/json'

    date = rfc_1123_date()
    method = PUT

    authorization_string = authorization_header(
        access_key=vuforia_database_keys.server_access_key,
        secret_key=vuforia_database_keys.server_secret_key,
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

    request = requests.Request(
        method=method,
        url=urljoin(base=VWS_HOST, url=request_path),
        headers=headers,
        data=content,
    )

    prepared_request = request.prepare()  # type: ignore

    return TargetAPIEndpoint(
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        prepared_request=prepared_request,
    )
