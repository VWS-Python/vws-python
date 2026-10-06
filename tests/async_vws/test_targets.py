"""Tests for `AsyncVWS` targets.

Test for deleting a target.
"""

from __future__ import annotations

import base64
import uuid
from typing import TYPE_CHECKING, BinaryIO

import pytest

# pytest-beartype resolves fixture annotations at runtime.
from vws import AsyncCloudRecoService, AsyncVWS  # noqa: TC001
from vws.reports import (
    TargetRecord,
    TargetStatuses,
)

if TYPE_CHECKING:
    import io


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="application_metadata",
    argvalues=[None, b"a"],
)
@pytest.mark.parametrize(
    argnames="active_flag",
    argvalues=[True, False],
)
async def test_add_target(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
    application_metadata: bytes | None,
    async_cloud_reco_client: AsyncCloudRecoService,
    active_flag: bool,
) -> None:
    """No exception is raised when adding one target."""
    name = "x"
    width = 1
    if application_metadata is None:
        encoded_metadata = None
    else:
        encoded_metadata_bytes = base64.b64encode(
            s=application_metadata,
        )
        encoded_metadata = encoded_metadata_bytes.decode(
            encoding="utf-8",
        )

    target_id = await async_vws_client.add_target(
        name=name,
        width=width,
        image=image,
        application_metadata=encoded_metadata,
        active_flag=active_flag,
    )
    target_record = (
        await async_vws_client.get_target_record(
            target_id=target_id,
        )
    ).target_record
    assert target_record.name == name
    assert target_record.width == width
    assert target_record.active_flag is active_flag
    await async_vws_client.wait_for_target_processed(
        target_id=target_id,
    )
    matching_targets = await async_cloud_reco_client.query(
        image=image,
    )
    if active_flag:
        [matching_target] = matching_targets
        assert matching_target.target_id == target_id
        assert matching_target.target_data is not None
        query_metadata = matching_target.target_data.application_metadata
        assert query_metadata == encoded_metadata
    else:
        assert matching_targets == []


@pytest.mark.asyncio
async def test_add_two_targets(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """No exception is raised when adding two targets with
    different names.

    This demonstrates that the image seek position is not
    changed.
    """
    for name in ("a", "b"):
        await async_vws_client.add_target(
            name=name,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )


@pytest.mark.asyncio
async def test_list_targets(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to get a list of target IDs."""
    id_1 = await async_vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    id_2 = await async_vws_client.add_target(
        name="a",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    targets = await async_vws_client.list_targets()
    assert sorted(targets) == sorted([id_1, id_2])


@pytest.mark.asyncio
async def test_delete_target(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to delete a target."""
    target_id = await async_vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )

    await async_vws_client.wait_for_target_processed(
        target_id=target_id,
    )
    targets = await async_vws_client.list_targets()
    assert targets == [target_id]
    await async_vws_client.delete_target(
        target_id=target_id,
    )
    targets = await async_vws_client.list_targets()
    assert targets == []


@pytest.mark.asyncio
async def test_get_target_record(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """Details of a target are returned by
    ``get_target_record``.
    """
    target_id = await async_vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )

    result = await async_vws_client.get_target_record(
        target_id=target_id,
    )
    expected_target_record = TargetRecord(
        target_id=target_id,
        active_flag=True,
        name="x",
        width=1,
        tracking_rating=-1,
        reco_rating="",
    )

    assert result.target_record == expected_target_record
    assert result.status == TargetStatuses.PROCESSING


@pytest.mark.asyncio
async def test_get_duplicate_targets(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to get the IDs of similar targets."""
    target_id = await async_vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    similar_target_id = await async_vws_client.add_target(
        name="a",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )

    await async_vws_client.wait_for_target_processed(
        target_id=target_id,
    )
    await async_vws_client.wait_for_target_processed(
        target_id=similar_target_id,
    )
    duplicates = await async_vws_client.get_duplicate_targets(
        target_id=target_id,
    )
    assert duplicates == [similar_target_id]


@pytest.mark.asyncio
async def test_update_target(
    *,
    async_vws_client: AsyncVWS,
    async_cloud_reco_client: AsyncCloudRecoService,
    image: io.BytesIO | BinaryIO,
    different_high_quality_image: io.BytesIO,
) -> None:
    """It is possible to update a target."""
    target_id = await async_vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    await async_vws_client.wait_for_target_processed(
        target_id=target_id,
    )
    [matching_target] = await async_cloud_reco_client.query(
        image=image,
    )
    assert matching_target.target_id == target_id
    query_target_data = matching_target.target_data
    assert query_target_data is not None
    assert query_target_data.application_metadata is None

    new_name = uuid.uuid4().hex
    new_width = 2.0
    new_application_metadata = base64.b64encode(
        s=b"a",
    ).decode(encoding="ascii")
    await async_vws_client.update_target(
        target_id=target_id,
        name=new_name,
        width=new_width,
        active_flag=True,
        image=different_high_quality_image,
        application_metadata=new_application_metadata,
    )

    await async_vws_client.wait_for_target_processed(
        target_id=target_id,
    )
    target_details = await async_vws_client.get_target_record(
        target_id=target_id,
    )
    assert target_details.target_record.name == new_name
    assert target_details.target_record.active_flag


@pytest.mark.asyncio
async def test_no_fields_given(
    *,
    async_vws_client: AsyncVWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to give no update fields."""
    target_id = await async_vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    await async_vws_client.wait_for_target_processed(
        target_id=target_id,
    )
    await async_vws_client.update_target(
        target_id=target_id,
    )
