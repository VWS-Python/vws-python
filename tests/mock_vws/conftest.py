"""
Configuration, plugins and fixtures for `pytest`.
"""

import os
import uuid
# This is used in a type hint which linters not pick up on.
from typing import Any  # noqa: F401 pylint: disable=unused-import
from typing import Generator

import pytest
import requests
from _pytest.fixtures import SubRequest
from requests import codes
from requests_mock import DELETE, GET, POST, PUT
from retrying import retry

from common.constants import ResultCodes
from mock_vws import MockVWS
from tests.mock_vws.utils import Endpoint
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


@retry(
    stop_max_delay=2 * 60 * 1000,
    wait_fixed=3 * 1000,
)
def _delete_target(vuforia_server_credentials: VuforiaServerCredentials,
                   target: str) -> None:
    """
    Delete a given target.

    Args:
        vuforia_server_credentials: The credentials to the Vuforia target
            database to delete the target in.
        target: The ID of the target to delete.

    Raises:
        AssertionError: The deletion was not a success.
    """
    date = rfc_1123_date()

    authorization_string = authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=DELETE,
        content=b'',
        content_type='',
        date=date,
        request_path='/targets/{target}'.format(target=target),
    )

    headers = {
        "Authorization": authorization_string,
        "Date": date,
    }

    response = requests.request(
        method=DELETE,
        url='https://vws.vuforia.com/targets/{target}'.format(target=target),
        headers=headers,
        data=b'',
    )

    result_code = response.json()['result_code']
    error_message = (
        'Deleting a target failed. '
        'The result code returned was: {result_code}. '
        'Perhaps wait and try again. '
        'However, sometimes targets get stuck on Vuforia, '
        'and a new testing database is required.'
    ).format(result_code=result_code)

    acceptable_results = (
        ResultCodes.SUCCESS.value,
        ResultCodes.UNKNOWN_TARGET.value,
    )
    assert result_code in acceptable_results, error_message


def _delete_all_targets(vuforia_server_credentials: VuforiaServerCredentials,
                        ) -> None:
    """
    Delete all targets.

    Args:
        vuforia_server_credentials: The credentials to the Vuforia target
            database to delete all targets in.
    """
    date = rfc_1123_date()

    authorization_string = authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        content_type='',
        date=date,
        request_path='/targets',
    )

    headers = {
        "Authorization": authorization_string,
        "Date": date,
    }

    response = requests.request(
        method=GET,
        url='https://vws.vuforia.com/targets',
        headers=headers,
        data=b'',
    )
    targets = response.json()['results']

    for target in targets:
        _delete_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target=target,
        )


@pytest.fixture(params=[True, False], ids=['Real Vuforia', 'Mock Vuforia'])
def verify_mock_vuforia(request: SubRequest,
                        vuforia_server_credentials: VuforiaServerCredentials,
                        ) -> Generator:
    """
    Using this fixture in a test will make it run twice. Once with the real
    Vuforia, and once with the mock.

    This is useful for verifying the mock.
    """
    skip_real = os.getenv('SKIP_REAL') == '1'
    skip_mock = os.getenv('SKIP_MOCK') == '1'

    use_real_vuforia = request.param

    if use_real_vuforia and skip_real:  # pragma: no cover
        pytest.skip()

    if not use_real_vuforia and skip_mock:  # pragma: no cover
        pytest.skip()

    if use_real_vuforia:
        _delete_all_targets(
            vuforia_server_credentials=vuforia_server_credentials,
        )
        yield
    else:
        with MockVWS():
            yield


@pytest.fixture()
def add_target() -> Endpoint:
    """
    Return details of the endpoint for adding a target.
    """
    data = {}  # type: Dict[str, Any]
    return Endpoint(
        example_path='/targets',
        method=POST,
        # We expect a bad request error because we have not given the required
        # JSON body elements.
        successful_headers_status_code=codes.BAD_REQUEST,
        successful_headers_result_code=ResultCodes.FAIL,
        content_type='application/json',
        content=bytes(str(data), encoding='utf-8'),
    )


@pytest.fixture()
def delete_target() -> Endpoint:
    """
    Return details of the endpoint for deleting a target.
    """
    example_path = '/targets/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=DELETE,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def database_summary() -> Endpoint:
    """
    Return details of the endpoint for getting details about the database.
    """
    return Endpoint(
        example_path='/summary',
        method=GET,
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def get_duplicates() -> Endpoint:
    """
    Return details of the endpoint for getting potential duplicates of a
    target.
    """
    example_path = '/duplicates/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=GET,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def get_target() -> Endpoint:
    """
    Return details of the endpoint for getting details of a target.
    """
    example_path = '/targets/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=GET,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def target_list() -> Endpoint:
    """
    Return details of the endpoint for getting a list of targets.
    """
    return Endpoint(
        example_path='/targets',
        method=GET,
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def target_summary() -> Endpoint:
    """
    Return details of the endpoint for getting a summary report of a target.
    """
    example_path = '/summary/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=GET,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def update_target() -> Endpoint:
    """
    Return details of the endpoint for updating a target.
    """
    data = {}  # type: Dict[str, Any]
    example_path = '/targets/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=PUT,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type='application/json',
        content=bytes(str(data), encoding='utf-8'),
    )


@pytest.fixture(params=[
    'delete_target',
    'get_target',
    'get_duplicates',
    'target_summary',
    'update_target',
])
def endpoint_which_takes_target_id(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which takes a target ID in the path.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    'database_summary',
    'delete_target',
    'get_duplicates',
    'get_target',
    'target_list',
    'target_summary',
])
def endpoint_no_data(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which does not take any JSON data.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    'add_target',
    'update_target',
])
def endpoint_which_takes_data(request: SubRequest) -> Endpoint:
    """
    XXX
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    'add_target',
    'database_summary',
    'delete_target',
    'get_duplicates',
    'get_target',
    'target_list',
    'target_summary',
    'update_target',
])
def endpoint(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint.
    """
    return request.getfixturevalue(request.param)
