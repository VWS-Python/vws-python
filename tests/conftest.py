"""
Configuration, plugins and fixtures for `pytest`.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, BinaryIO

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from vws import VWS, CloudRecoService

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture(name="_mock_database")
def mock_database() -> Generator[VuforiaDatabase, None, None]:
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
    A VWS client which connects to a mock database.
    """
    return VWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
    )


@pytest.fixture()
def cloud_reco_client(_mock_database: VuforiaDatabase) -> CloudRecoService:
    """
    A ``CloudRecoService`` client which connects to a mock database.
    """
    return CloudRecoService(
        client_access_key=_mock_database.client_access_key,
        client_secret_key=_mock_database.client_secret_key,
    )


@pytest.fixture()
def image_file(
    high_quality_image: io.BytesIO,
    tmp_path: Path,
) -> Generator[io.BufferedRandom, None, None]:
    """An image file object."""
    file = tmp_path / "image.jpg"
    file.touch()
    with file.open("r+b") as fileobj:
        buffer = high_quality_image.getvalue()
        fileobj.write(buffer)
        yield fileobj


@pytest.fixture(params=["high_quality_image", "image_file"])
def image(
    request: pytest.FixtureRequest,
) -> BinaryIO:
    """An image in any of the types that the API accepts."""
    result = request.getfixturevalue(request.param)
    assert isinstance(result, io.BytesIO | io.BufferedRandom)
    return result
