"""Tests for `AsyncVWS` configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from vws import AsyncVWS

if TYPE_CHECKING:
    import io


@pytest.mark.asyncio
async def test_custom_base_url(
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to add a target to a database under a
    custom VWS URL.
    """
    base_vws_url = "http://example.com"
    with MockVWS(base_vws_url=base_vws_url) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        async_vws_client = AsyncVWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            base_vws_url=base_vws_url,
        )

        await async_vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
