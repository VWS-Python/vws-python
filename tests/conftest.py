"""
Configuration, plugins and fixtures for `pytest`.
"""

from typing import Iterator

import pytest
from mock_vws import MockVWS

from vws import VWS

pytest_plugins = [  # pylint: disable=invalid-name
    'tests.fixtures.images',
]


@pytest.fixture()
def client() -> Iterator[VWS]:
    """
    Yield a VWS client which connects to a mock.
    """
    with MockVWS() as mock:
        vws_client = VWS(
            server_access_key=mock.server_access_key,
            server_secret_key=mock.server_secret_key,
        )

        yield vws_client
