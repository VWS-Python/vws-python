"""Tests for async helper functions for managing a Vuforia database."""

import base64
import io
import uuid
from typing import BinaryIO

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from vws import AsyncCloudRecoService, AsyncVuMarkService, AsyncVWS
from vws.exceptions.custom_exceptions import (
    TargetProcessingTimeoutError,
)
from vws.reports import (
    DatabaseSummaryReport,
    TargetRecord,
    TargetStatuses,
)
from vws.vumark_accept import VuMarkAccept


class TestAddTarget:
    """Tests for adding a target."""

    @staticmethod
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

    @staticmethod
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


class TestCustomBaseVWSURL:
    """Tests for using a custom base VWS URL."""

    @staticmethod
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


class TestListTargets:
    """Tests for listing targets."""

    @staticmethod
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


class TestDelete:
    """Test for deleting a target."""

    @staticmethod
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
        assert target_id in targets
        await async_vws_client.delete_target(
            target_id=target_id,
        )
        targets = await async_vws_client.list_targets()
        assert target_id not in targets


class TestGetTargetSummaryReport:
    """Tests for getting a summary report for a target."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_target_summary_report(
        *,
        async_vws_client: AsyncVWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """Details of a target are returned by
        ``get_target_summary_report``.
        """
        target_name = uuid.uuid4().hex
        target_id = await async_vws_client.add_target(
            name=target_name,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )

        report = await async_vws_client.get_target_summary_report(
            target_id=target_id,
        )

        assert report.target_name == target_name
        assert report.active_flag is True
        assert report.total_recos == 0


class TestGetDatabaseSummaryReport:
    """Tests for getting a summary report for a database."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_target(
        async_vws_client: AsyncVWS,
    ) -> None:
        """Details of a database are returned by
        ``get_database_summary_report``.
        """
        report = await async_vws_client.get_database_summary_report()

        assert isinstance(report, DatabaseSummaryReport)
        assert report.active_images == 0


class TestGetTargetRecord:
    """Tests for getting a record of a target."""

    @staticmethod
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


class TestWaitForTargetProcessed:
    """Tests for waiting for a target to be processed."""

    @staticmethod
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

    @staticmethod
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


class TestGetDuplicateTargets:
    """Tests for getting duplicate targets."""

    @staticmethod
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


class TestUpdateTarget:
    """Tests for updating a target."""

    @staticmethod
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

    @staticmethod
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


class TestGenerateVumarkInstance:
    """Tests for generating VuMark instances."""

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames=("accept", "expected_prefix"),
        argvalues=[
            pytest.param(
                VuMarkAccept.PNG,
                b"\x89PNG\r\n\x1a\n",
                id="png",
            ),
            pytest.param(
                VuMarkAccept.SVG,
                b"<",
                id="svg",
            ),
            pytest.param(
                VuMarkAccept.PDF,
                b"%PDF",
                id="pdf",
            ),
        ],
    )
    async def test_generate_vumark_instance(
        *,
        async_vumark_service_client: AsyncVuMarkService,
        vumark_target_id: str,
        accept: VuMarkAccept,
        expected_prefix: bytes,
    ) -> None:
        """The returned bytes match the requested format."""
        result = await async_vumark_service_client.generate_vumark_instance(
            target_id=vumark_target_id,
            instance_id="12345",
            accept=accept,
        )
        assert result.startswith(expected_prefix)
