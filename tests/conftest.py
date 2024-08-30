"""
Configuration, plugins and fixtures for `pytest`.
"""

import io
from collections.abc import Generator
from pathlib import Path
from typing import BinaryIO, Literal

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import VWS, CloudRecoService


@pytest.fixture(name="_mock_database")
def mock_database() -> Generator[VuforiaDatabase, None, None]:
    """
    Yield a mock ``VuforiaDatabase``.
    """
    # We use a low processing time so that tests run quickly.
    with MockVWS(processing_time_seconds=0.2) as mock:
        database = VuforiaDatabase()
        mock.add_database(database=database)
        yield database


@pytest.fixture
def vws_client(_mock_database: VuforiaDatabase) -> VWS:
    """
    A VWS client which connects to a mock database.
    """
    return VWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
    )


@pytest.fixture
def cloud_reco_client(_mock_database: VuforiaDatabase) -> CloudRecoService:
    """
    A ``CloudRecoService`` client which connects to a mock database.
    """
    return CloudRecoService(
        client_access_key=_mock_database.client_access_key,
        client_secret_key=_mock_database.client_secret_key,
    )


@pytest.fixture(name="image_file", params=["r+b", "rb"])
def image_file_fixture(
    high_quality_image: io.BytesIO,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> Generator[BinaryIO, None, None]:
    """An image file object."""
    file = tmp_path / "image.jpg"
    buffer = high_quality_image.getvalue()
    file.write_bytes(data=buffer)
    mode: Literal["r+b", "rb"] = request.param
    with file.open(mode=mode) as file_obj:
        yield file_obj


@pytest.fixture(params=["high_quality_image", "image_file"])
def image(
    request: pytest.FixtureRequest,
    high_quality_image: io.BytesIO,
    image_file: BinaryIO,
) -> io.BytesIO | BinaryIO:
    """An image in any of the types that the API accepts."""
    if request.param == "high_quality_image":
        return high_quality_image
    return image_file
