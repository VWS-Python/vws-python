"""Tests for `AsyncVWS` processing."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Literal

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from tests.image_factory import IMAGE_CASES, ImageFactory
from vws import AsyncVWS
from vws.exceptions.custom_exceptions import (
    TargetProcessingTimeoutError,
)
from vws.reports import (
    TargetStatuses,
)

if TYPE_CHECKING:
    import io


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
async def test_wait_for_target_processed(
    *,
    async_vws_client: AsyncVWS,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """It is possible to wait until a target is processed."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = await async_vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    report = await async_vws_client.get_target_summary_report(
        target_id=target_id,
    )
    assert report.status == TargetStatuses.PROCESSING
    await async_vws_client.wait_for_target_processed(
        target_id=target_id,
    )
    report = await async_vws_client.get_target_summary_report(
        target_id=target_id,
    )
    assert report.status != TargetStatuses.PROCESSING


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
async def test_custom_timeout(
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """It is possible to set a maximum timeout."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    with MockVWS(processing_time_seconds=0.5) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        async_vws_client = AsyncVWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        target_id = await async_vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )

        with pytest.raises(
            expected_exception=(TargetProcessingTimeoutError),
        ):
            await async_vws_client.wait_for_target_processed(
                target_id=target_id,
                timeout_seconds=0.1,
            )
