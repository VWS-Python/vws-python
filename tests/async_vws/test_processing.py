"""Tests for `AsyncVWS` processing."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

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
async def test_wait_for_target_processed(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to wait until a target is processed."""
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
async def test_custom_timeout(
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to set a maximum timeout."""
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
