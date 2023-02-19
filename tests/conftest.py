"""
Configuration, plugins and fixtures for `pytest`.
"""

from collections.abc import Iterator

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from vws import VWS, CloudRecoService


@pytest.fixture(name="_mock_database")
def mock_database() -> Iterator[VuforiaDatabase]:
    """
    Yield a mock ``VuforiaDatabase``.
    """
    with MockVWS() as mock:
        database = VuforiaDatabase()
        mock.add_database(database=database)
        yield database


@pytest.fixture()
def vws_client(_mock_database: VuforiaDatabase) -> VWS:
    """
    Yield a VWS client which connects to a mock database.
    """
    return VWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
    )


@pytest.fixture()
def cloud_reco_client(_mock_database: VuforiaDatabase) -> CloudRecoService:
    """
    Yield a ``CloudRecoService`` client which connects to a mock database.
    """
    return CloudRecoService(
        client_access_key=_mock_database.client_access_key,
        client_secret_key=_mock_database.client_secret_key,
    )
