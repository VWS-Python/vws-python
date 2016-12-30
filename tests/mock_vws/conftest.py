"""
Configuration, plugins and fixtures for `pytest`.
"""

from typing import Generator

import pytest
from _pytest.fixtures import SubRequest
from requests_mock import GET

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
def target_list() -> Endpoint:
    """
    Return details of the endpoint for getting a list of targets.
    """
    return Endpoint(path='/targets', method=GET)


@pytest.fixture()
def get_duplicates() -> Endpoint:
    """
    Return details of the endpoint for getting details of a target.
    """
    return Endpoint(path='/duplicates', method=GET)


@pytest.fixture(params=['target_list', 'get_duplicates'])
def endpoint_which_takes_target_id(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which takes a target ID in the path.
    """
    return request.getfixturevalue(request.param)
