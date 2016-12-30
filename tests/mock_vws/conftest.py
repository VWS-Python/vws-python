"""
Configuration, plugins and fixtures for `pytest`.
"""

from typing import Generator

import pytest
from _pytest.fixtures import SubRequest

from mock_vws import MockVWS


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
