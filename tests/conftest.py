"""Configuration, plugins and fixtures for `pytest`."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from mock_vws import MockVWS
from mock_vws.database import VuMarkDatabase
from mock_vws.target import VuMarkTarget

from vws import (
    AsyncModelTargetService,
    AsyncVuMarkService,
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
_MODEL_TARGET_CLIENT_CREDENTIALS = ("client-id", "client-secret")


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
        client_secret=_MODEL_TARGET_CLIENT_CREDENTIALS[1],
    )


@pytest_asyncio.fixture
async def async_model_target_client(
    *,
    _mock_model_targets: None,
) -> AsyncGenerator[AsyncModelTargetService]:
    """An async ``ModelTargetService`` client which connects to a mock."""
    async with AsyncModelTargetService(
        client_id=_MODEL_TARGET_CLIENT_ID,
        client_secret=_MODEL_TARGET_CLIENT_CREDENTIALS[1],
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
