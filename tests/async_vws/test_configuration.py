"""Tests for `AsyncVWS` configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Literal

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from tests.image_factory import IMAGE_CASES, ImageFactory
from vws import AsyncVWS

if TYPE_CHECKING:
    import io


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
async def test_custom_base_url(
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """It is possible to add a target to a database under a
    custom VWS URL.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
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
