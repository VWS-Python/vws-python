"""
Configuration, plugins and fixtures for `pytest`.
"""

import uuid
from typing import Generator

import pytest
from _pytest.fixtures import SubRequest
from requests import codes
from requests_mock import DELETE, GET, POST

from common.constants import ResultCodes
from mock_vws import MockVWS
from tests.mock_vws.utils import Endpoint


@pytest.fixture(params=[True, False], ids=['Real Vuforia', 'Mock Vuforia'])
def verify_mock_vuforia(request: SubRequest) -> Generator:
    """
    Using this fixture in a test will make it run twice. Once with the real
    Vuforia, and once with the mock.

    This is useful for verifying the mock.
    """
    use_real_vuforia = request.param
    if use_real_vuforia:
        yield
    else:
        with MockVWS():
            yield


@pytest.fixture()
def add_target() -> Endpoint:
    """
    Return details of the endpoint for adding a target.
    """
    return Endpoint(
        example_path='/targets',
        method=POST,
        successful_headers_status_code=codes.CREATED,
        successful_headers_result_code=ResultCodes.TARGET_CREATED,
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
    )


@pytest.fixture(params=['get_target', 'get_duplicates'])
def endpoint_which_takes_target_id(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which takes a target ID in the path.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    'add_target',
    'database_summary',
    'get_duplicates',
    'get_target',
    'target_list',
])
def endpoint(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint.
    """
    return request.getfixturevalue(request.param)
