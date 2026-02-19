"""Configuration, plugins and fixtures for `pytest`."""

import io
from collections.abc import Generator
from pathlib import Path
from typing import BinaryIO, Literal

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase, VuMarkDatabase, VuMarkTarget

from vws import VWS, CloudRecoService, VuMarkService


@pytest.fixture(name="_mock_database")
def fixture_mock_database() -> Generator[CloudDatabase]:
    """Yield a mock ``CloudDatabase``."""
    # We use a low processing time so that tests run quickly.
    with MockVWS(processing_time_seconds=0.2) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        yield database


@pytest.fixture(name="_mock_vumark_database")
def fixture_mock_vumark_database() -> Generator[VuMarkDatabase]:
    """Yield a mock ``VuMarkDatabase`` with a template target."""
    vumark_target = VuMarkTarget(name="vumark-template")
    with MockVWS() as mock:
        database = VuMarkDatabase(vumark_targets={vumark_target})
        mock.add_vumark_database(vumark_database=database)
        yield database


@pytest.fixture
def vumark_service_client(
    _mock_vumark_database: VuMarkDatabase,
) -> VuMarkService:
    """A ``VuMarkService`` client which connects to a mock VuMark database."""
    return VuMarkService(
        server_access_key=_mock_vumark_database.server_access_key,
        server_secret_key=_mock_vumark_database.server_secret_key,
    )


@pytest.fixture
def vumark_target_id(_mock_vumark_database: VuMarkDatabase) -> str:
    """The ID of the VuMark template target."""
    (target,) = _mock_vumark_database.vumark_targets
    return target.target_id


@pytest.fixture
def vws_client(_mock_database: CloudDatabase) -> VWS:
    """A VWS client which connects to a mock database."""
    return VWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
    )


@pytest.fixture
def cloud_reco_client(_mock_database: CloudDatabase) -> CloudRecoService:
    """A ``CloudRecoService`` client which connects to a mock database."""
    return CloudRecoService(
        client_access_key=_mock_database.client_access_key,
        client_secret_key=_mock_database.client_secret_key,
    )


@pytest.fixture(name="image_file", params=["r+b", "rb"])
def fixture_image_file(
    high_quality_image: io.BytesIO,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> Generator[BinaryIO]:
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
