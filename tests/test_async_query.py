"""Tests for the ``AsyncCloudRecoService`` querying functionality."""

import io
import uuid
from typing import BinaryIO

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from vws import AsyncCloudRecoService, AsyncVWS
from vws.include_target_data import CloudRecoIncludeTargetData


class TestQuery:
    """Tests for making async image queries."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_no_matches(
        *,
        async_cloud_reco_client: AsyncCloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """An empty list is returned if there are no matches."""
        result = await async_cloud_reco_client.query(
            image=image,
        )
        assert result == []

    @staticmethod
    @pytest.mark.asyncio
    async def test_match(
        *,
        async_vws_client: AsyncVWS,
        async_cloud_reco_client: AsyncCloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """Details of matching targets are returned."""
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


class TestCustomBaseVWQURL:
    """Tests for using a custom base VWQ URL."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_custom_base_url(
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """It is possible to query a target in a database under
        a custom VWQ URL.
        """
        base_vwq_url = "http://example.com"
        with MockVWS(base_vwq_url=base_vwq_url) as mock:
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

            await async_vws_client.wait_for_target_processed(
                target_id=target_id,
            )

            async_cloud_reco_client = AsyncCloudRecoService(
                client_access_key=database.client_access_key,
                client_secret_key=database.client_secret_key,
                base_vwq_url=base_vwq_url,
            )

            matches = await async_cloud_reco_client.query(
                image=image,
            )
            assert len(matches) == 1
            match = matches[0]
            assert match.target_id == target_id


class TestMaxNumResults:
    """Tests for the ``max_num_results`` parameter of
    ``query``.
    """

    @staticmethod
    @pytest.mark.asyncio
    async def test_custom(
        *,
        async_vws_client: AsyncVWS,
        async_cloud_reco_client: AsyncCloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """It is possible to set a custom
        ``max_num_results``.
        """
        target_id = await async_vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = await async_vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_3 = await async_vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        await async_vws_client.wait_for_target_processed(
            target_id=target_id,
        )
        await async_vws_client.wait_for_target_processed(
            target_id=target_id_2,
        )
        await async_vws_client.wait_for_target_processed(
            target_id=target_id_3,
        )
        max_num_results = 2
        matches = await async_cloud_reco_client.query(
            image=image,
            max_num_results=max_num_results,
        )
        assert len(matches) == max_num_results


class TestIncludeTargetData:
    """Tests for the ``include_target_data`` parameter of
    ``query``.
    """

    @staticmethod
    @pytest.mark.asyncio
    async def test_none(
        *,
        async_vws_client: AsyncVWS,
        async_cloud_reco_client: AsyncCloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """When ``CloudRecoIncludeTargetData.NONE`` is given,
        target data is not returned in any match.
        """
        target_id = await async_vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        await async_vws_client.wait_for_target_processed(
            target_id=target_id,
        )
        [match] = await async_cloud_reco_client.query(
            image=image,
            include_target_data=(CloudRecoIncludeTargetData.NONE),
        )
        assert match.target_data is None

    @staticmethod
    @pytest.mark.asyncio
    async def test_all(
        *,
        async_vws_client: AsyncVWS,
        async_cloud_reco_client: AsyncCloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """When ``CloudRecoIncludeTargetData.ALL`` is given,
        target data is returned in all matches.
        """
        target_id = await async_vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = await async_vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        await async_vws_client.wait_for_target_processed(
            target_id=target_id,
        )
        await async_vws_client.wait_for_target_processed(
            target_id=target_id_2,
        )
        top_match, second_match = await async_cloud_reco_client.query(
            image=image,
            max_num_results=2,
            include_target_data=(CloudRecoIncludeTargetData.ALL),
        )
        assert top_match.target_data is not None
        assert second_match.target_data is not None
