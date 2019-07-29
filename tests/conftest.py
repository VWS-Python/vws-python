"""
Configuration, plugins and fixtures for `pytest`.
"""

from typing import Iterator

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import VWS

pytest_plugins = [  # pylint: disable=invalid-name
    'tests.fixtures.images',
]


@pytest.fixture()
def _mock_database() -> Iterator[VuforiaDatabase]:
    with MockVWS() as mock:
        database = VuforiaDatabase()
        mock.add_database(database=database)
        yield database


@pytest.fixture()
def client(_mock_database: VuforiaDatabase) -> Iterator[VWS]:
    """
    # TODO rename this fixture

    Yield a VWS client which connects to a mock.
    """
    vws_client = VWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
    )

    yield vws_client


@pytest.fixture()
def cloud_reco_client(_mock_database: VuforiaDatabase) -> Iterator[VWS]:
    """
    # TODO rename this fixture

    Yield a VWS client which connects to a mock.
    """
    vws_client = VWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
    )

    yield vws_client
