"""Configuration, plugins and fixtures for `pytest`."""

import datetime
import io  # noqa: TC003
from collections.abc import AsyncGenerator, Generator  # noqa: TC003
from pathlib import Path  # noqa: TC003
from typing import BinaryIO, Literal

import pytest
import pytest_asyncio
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase, VuMarkDatabase
from mock_vws.target import VuMarkTarget

from vws import (
    VWS,
    AsyncCloudRecoService,
    AsyncModelTargetService,
    AsyncVuMarkService,
    AsyncVWS,
    CloudRecoService,
    ModelTargetService,
    VuMarkService,
)
from vws.model_target_datasets import (
    CadDataFormat,
    GuideViewPosition,
    ModelTargetModel,
    ModelTargetView,
)

# The mock accepts one hard-coded pair of Model Target Web API OAuth2
# credentials, which it does not expose.
_MODEL_TARGET_CLIENT_ID = "client-id"
_MODEL_TARGET_CLIENT_SECRET = "client-secret"  # noqa: S105


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
    *,
    _mock_vumark_database: VuMarkDatabase,
) -> VuMarkService:
    """A ``VuMarkService`` client which connects to a mock VuMark database."""
    return VuMarkService(
        server_access_key=_mock_vumark_database.server_access_key,
        server_secret_key=_mock_vumark_database.server_secret_key,
    )


@pytest.fixture
def vumark_target_id(*, _mock_vumark_database: VuMarkDatabase) -> str:
    """The ID of the VuMark template target."""
    (target,) = _mock_vumark_database.vumark_targets
    return target.target_id


@pytest.fixture
def vws_client(*, _mock_database: CloudDatabase) -> VWS:
    """A VWS client which connects to a mock database."""
    return VWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
        database_id=_mock_database.database_id,
    )


@pytest.fixture
def cloud_reco_client(*, _mock_database: CloudDatabase) -> CloudRecoService:
    """A ``CloudRecoService`` client which connects to a mock database."""
    return CloudRecoService(
        client_access_key=_mock_database.client_access_key,
        client_secret_key=_mock_database.client_secret_key,
    )


@pytest_asyncio.fixture
async def async_vws_client(
    *,
    _mock_database: CloudDatabase,
) -> AsyncGenerator[AsyncVWS]:
    """An async VWS client which connects to a mock database."""
    async with AsyncVWS(
        server_access_key=_mock_database.server_access_key,
        server_secret_key=_mock_database.server_secret_key,
        database_id=_mock_database.database_id,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def async_cloud_reco_client(
    *,
    _mock_database: CloudDatabase,
) -> AsyncGenerator[AsyncCloudRecoService]:
    """An async ``CloudRecoService`` client which connects to a mock
    database.
    """
    async with AsyncCloudRecoService(
        client_access_key=_mock_database.client_access_key,
        client_secret_key=_mock_database.client_secret_key,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def async_vumark_service_client(
    *,
    _mock_vumark_database: VuMarkDatabase,
) -> AsyncGenerator[AsyncVuMarkService]:
    """An async ``VuMarkService`` client which connects to a mock VuMark
    database.
    """
    async with AsyncVuMarkService(
        server_access_key=_mock_vumark_database.server_access_key,
        server_secret_key=_mock_vumark_database.server_secret_key,
    ) as client:
        yield client


@pytest.fixture(name="_mock_model_targets")
def fixture_mock_model_targets() -> Generator[None]:
    """Yield a mock which serves the Model Target Web API.

    The Model Target Web API is not tied to a VWS database, so no
    database is added.
    """
    # We use a low processing time so that tests run quickly.
    with MockVWS(processing_time_seconds=0.2):
        yield


@pytest.fixture
def model_target_client(
    *,
    _mock_model_targets: None,
) -> ModelTargetService:
    """A ``ModelTargetService`` client which connects to a mock."""
    return ModelTargetService(
        client_id=_MODEL_TARGET_CLIENT_ID,
        client_secret=_MODEL_TARGET_CLIENT_SECRET,
    )


@pytest_asyncio.fixture
async def async_model_target_client(
    *,
    _mock_model_targets: None,
) -> AsyncGenerator[AsyncModelTargetService]:
    """An async ``ModelTargetService`` client which connects to a mock."""
    async with AsyncModelTargetService(
        client_id=_MODEL_TARGET_CLIENT_ID,
        client_secret=_MODEL_TARGET_CLIENT_SECRET,
    ) as client:
        yield client


@pytest.fixture(name="model_target_model")
def fixture_model_target_model() -> ModelTargetModel:
    """A model which Vuforia accepts for dataset creation."""
    return ModelTargetModel(
        name="model",
        cad_data_url="https://example.com/model.zip",
        cad_data_format=CadDataFormat.ZIP,
        views=[
            ModelTargetView(
                name="front",
                guide_view_position=GuideViewPosition(
                    rotation=[0.0, 0.0, 0.0, 1.0],
                    translation=[0.0, 0.0, 1.0],
                ),
            ),
        ],
    )


@pytest.fixture(name="current_month")
def fixture_current_month() -> datetime.date:
    """The current month, as the first day of that month."""
    now = datetime.datetime.now(tz=datetime.UTC)
    return now.date().replace(day=1)


@pytest.fixture(name="report_month", params=["current", "previous"])
def fixture_report_month(*, request: pytest.FixtureRequest) -> datetime.date:
    """A month which a reco counts report can be requested for.

    Vuforia accepts only the current month and the previous month.
    """
    now = datetime.datetime.now(tz=datetime.UTC)
    first_of_month = now.date().replace(day=1)
    if request.param == "current":
        return first_of_month

    return first_of_month - datetime.timedelta(days=1)


@pytest.fixture(name="image_file", params=["r+b", "rb"])
def fixture_image_file(
    *,
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
    *,
    request: pytest.FixtureRequest,
    high_quality_image: io.BytesIO,
    image_file: BinaryIO,
) -> io.BytesIO | BinaryIO:
    """An image in any of the types that the API accepts."""
    if request.param == "high_quality_image":
        return high_quality_image
    return image_file
