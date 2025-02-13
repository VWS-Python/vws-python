"""
Tests for helper functions for managing a Vuforia database.
"""

import base64
import datetime
import io
import secrets
import uuid
from typing import BinaryIO

import pytest
from freezegun import freeze_time
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import VWS, CloudRecoService
from vws.exceptions.custom_exceptions import TargetProcessingTimeoutError
from vws.reports import (
    DatabaseSummaryReport,
    TargetRecord,
    TargetStatuses,
    TargetSummaryReport,
)


class TestAddTarget:
    """
    Tests for adding a target.
    """

    @staticmethod
    @pytest.mark.parametrize(
        argnames="application_metadata",
        argvalues=[None, b"a"],
    )
    @pytest.mark.parametrize(argnames="active_flag", argvalues=[True, False])
    def test_add_target(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
        application_metadata: bytes | None,
        cloud_reco_client: CloudRecoService,
        *,
        active_flag: bool,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        name = "x"
        width = 1
        if application_metadata is None:
            encoded_metadata = None
        else:
            encoded_metadata_bytes = base64.b64encode(s=application_metadata)
            encoded_metadata = encoded_metadata_bytes.decode(encoding="utf-8")

        target_id = vws_client.add_target(
            name=name,
            width=width,
            image=image,
            application_metadata=encoded_metadata,
            active_flag=active_flag,
        )
        target_record = vws_client.get_target_record(
            target_id=target_id,
        ).target_record
        assert target_record.name == name
        assert target_record.width == width
        assert target_record.active_flag is active_flag
        vws_client.wait_for_target_processed(target_id=target_id)
        matching_targets = cloud_reco_client.query(image=image)
        if active_flag:
            [matching_target] = matching_targets
            assert matching_target.target_id == target_id
            assert matching_target.target_data is not None
            query_metadata = matching_target.target_data.application_metadata
            assert query_metadata == encoded_metadata
        else:
            assert matching_targets == []

    @staticmethod
    def test_add_two_targets(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """No exception is raised when adding two targets with different names.

        This demonstrates that the image seek position is not changed.
        """
        for name in ("a", "b"):
            vws_client.add_target(
                name=name,
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )


class TestCustomBaseVWSURL:
    """
    Tests for using a custom base VWS URL.
    """

    @staticmethod
    def test_custom_base_url(image: io.BytesIO | BinaryIO) -> None:
        """
        It is possible to use add a target to a database under a custom VWS
        URL.
        """
        base_vws_url = "http://example.com"
        with MockVWS(base_vws_url=base_vws_url) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
                base_vws_url=base_vws_url,
            )

            vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )


class TestListTargets:
    """
    Tests for listing targets.
    """

    @staticmethod
    def test_list_targets(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        It is possible to get a list of target IDs.
        """
        id_1 = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        id_2 = vws_client.add_target(
            name="a",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        assert sorted(vws_client.list_targets()) == sorted([id_1, id_2])


class TestDelete:
    """
    Test for deleting a target.
    """

    @staticmethod
    def test_delete_target(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        It is possible to delete a target.
        """
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )

        vws_client.wait_for_target_processed(target_id=target_id)
        assert target_id in vws_client.list_targets()
        vws_client.delete_target(target_id=target_id)
        assert target_id not in vws_client.list_targets()


class TestGetTargetSummaryReport:
    """
    Tests for getting a summary report for a target.
    """

    @staticmethod
    def test_get_target_summary_report(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_summary_report``.
        """
        date = "2018-04-25"
        target_name = uuid.uuid4().hex
        with freeze_time(time_to_freeze=date):
            target_id = vws_client.add_target(
                name=target_name,
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )

        report = vws_client.get_target_summary_report(target_id=target_id)

        expected_report = TargetSummaryReport(
            status=TargetStatuses.SUCCESS,
            database_name=report.database_name,
            target_name=target_name,
            upload_date=datetime.date(year=2018, month=4, day=25),
            active_flag=True,
            tracking_rating=report.tracking_rating,
            total_recos=0,
            current_month_recos=0,
            previous_month_recos=0,
        )

        assert report.status == expected_report.status
        assert report.database_name == expected_report.database_name
        assert report.target_name == expected_report.target_name
        assert report.upload_date == expected_report.upload_date
        assert report.active_flag == expected_report.active_flag
        assert report.tracking_rating == expected_report.tracking_rating
        assert report.total_recos == expected_report.total_recos
        assert (
            report.current_month_recos == expected_report.current_month_recos
        )
        assert (
            report.previous_month_recos == expected_report.previous_month_recos
        )

        assert report == expected_report


class TestGetDatabaseSummaryReport:
    """
    Tests for getting a summary report for a database.
    """

    @staticmethod
    def test_get_target(vws_client: VWS) -> None:
        """
        Details of a database are returned by ``get_database_summary_report``.
        """
        report = vws_client.get_database_summary_report()

        expected_report = DatabaseSummaryReport(
            active_images=0,
            current_month_recos=0,
            failed_images=0,
            inactive_images=0,
            name=report.name,
            previous_month_recos=0,
            processing_images=0,
            reco_threshold=1000,
            request_quota=100000,
            request_usage=0,
            target_quota=1000,
            total_recos=0,
        )

        assert report.active_images == expected_report.active_images
        assert (
            report.current_month_recos == expected_report.current_month_recos
        )
        assert report.failed_images == expected_report.failed_images
        assert report.inactive_images == expected_report.inactive_images
        assert report.name == expected_report.name
        assert (
            report.previous_month_recos == expected_report.previous_month_recos
        )
        assert report.processing_images == expected_report.processing_images
        assert report.reco_threshold == expected_report.reco_threshold
        assert report.request_quota == expected_report.request_quota
        assert report.request_usage == expected_report.request_usage
        assert report.target_quota == expected_report.target_quota
        assert report.total_recos == expected_report.total_recos

        assert report == expected_report


class TestGetTargetRecord:
    """
    Tests for getting a record of a target.
    """

    @staticmethod
    def test_get_target_record(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_record``.
        """
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )

        result = vws_client.get_target_record(target_id=target_id)
        expected_target_record = TargetRecord(
            target_id=target_id,
            active_flag=True,
            name="x",
            width=1,
            tracking_rating=-1,
            reco_rating="",
        )

        assert result.target_record == expected_target_record

        assert (
            result.target_record.target_id == expected_target_record.target_id
        )
        assert (
            result.target_record.active_flag
            == expected_target_record.active_flag
        )
        assert result.target_record.name == expected_target_record.name
        assert result.target_record.width == expected_target_record.width
        assert (
            result.target_record.tracking_rating
            == expected_target_record.tracking_rating
        )
        assert (
            result.target_record.reco_rating
            == expected_target_record.reco_rating
        )

        assert result.status == TargetStatuses.PROCESSING

    @staticmethod
    def test_get_failed(
        vws_client: VWS,
        image_file_failed_state: io.BytesIO,
    ) -> None:
        """
        Check that the report works with a failed target.
        """
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image_file_failed_state,
            active_flag=True,
            application_metadata=None,
        )

        vws_client.wait_for_target_processed(target_id=target_id)
        result = vws_client.get_target_record(target_id=target_id)

        assert result.status == TargetStatuses.FAILED


class TestWaitForTargetProcessed:
    """
    Tests for waiting for a target to be processed.
    """

    @staticmethod
    def test_wait_for_target_processed(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        It is possible to wait until a target is processed.
        """
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        report = vws_client.get_target_summary_report(target_id=target_id)
        assert report.status == TargetStatuses.PROCESSING
        vws_client.wait_for_target_processed(target_id=target_id)
        report = vws_client.get_target_summary_report(target_id=target_id)
        assert report.status != TargetStatuses.PROCESSING

    @staticmethod
    def test_default_seconds_between_requests(
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        By default, 0.2 seconds are waited between polling requests.
        """
        with MockVWS(processing_time_seconds=0.5) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )

            vws_client.wait_for_target_processed(target_id=target_id)
            report = vws_client.get_database_summary_report()
            expected_requests = (
                # Add target request
                1
                +
                # Database summary request
                1
                +
                # Initial request
                1
                +
                # Request after 0.2 seconds - not processed
                1
                +
                # Request after 0.4 seconds - not processed
                # This assumes that there is less than 0.1 seconds taken
                # between the start of the target processing and the start of
                # waiting for the target to be processed.
                1
                +
                # Request after 0.6 seconds - processed
                1
            )
            # At the time of writing there is a bug which prevents request
            # usage from being tracked so we cannot track this.
            expected_requests = 0
            assert report.request_usage == expected_requests

    @staticmethod
    def test_custom_seconds_between_requests(
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        It is possible to customize the time waited between polling requests.
        """
        with MockVWS(processing_time_seconds=0.5) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )

            vws_client.wait_for_target_processed(
                target_id=target_id,
                seconds_between_requests=0.3,
            )
            report = vws_client.get_database_summary_report()
            expected_requests = (
                # Add target request
                1
                +
                # Database summary request
                1
                +
                # Initial request
                1
                +
                # Request after 0.3 seconds - not processed
                # This assumes that there is less than 0.2 seconds taken
                # between the start of the target processing and the start of
                # waiting for the target to be processed.
                1
                +
                # Request after 0.6 seconds - processed
                1
            )
            # At the time of writing there is a bug which prevents request
            # usage from being tracked so we cannot track this.
            expected_requests = 0
            assert report.request_usage == expected_requests

    @staticmethod
    def test_custom_timeout(image: io.BytesIO | BinaryIO) -> None:
        """
        It is possible to set a maximum timeout.
        """
        with MockVWS(processing_time_seconds=0.5) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )

            report = vws_client.get_target_summary_report(target_id=target_id)
            assert report.status == TargetStatuses.PROCESSING
            with pytest.raises(
                expected_exception=TargetProcessingTimeoutError
            ):
                vws_client.wait_for_target_processed(
                    target_id=target_id,
                    timeout_seconds=0.1,
                )

            vws_client.wait_for_target_processed(
                target_id=target_id,
                timeout_seconds=0.5,
            )
            report = vws_client.get_target_summary_report(target_id=target_id)
            assert report.status != TargetStatuses.PROCESSING


class TestGetDuplicateTargets:
    """
    Tests for getting duplicate targets.
    """

    @staticmethod
    def test_get_duplicate_targets(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        It is possible to get the IDs of similar targets.
        """
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        similar_target_id = vws_client.add_target(
            name="a",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )

        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=similar_target_id)
        duplicates = vws_client.get_duplicate_targets(target_id=target_id)
        assert duplicates == [similar_target_id]


class TestUpdateTarget:
    """
    Tests for updating a target.
    """

    @staticmethod
    def test_update_target(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
        different_high_quality_image: io.BytesIO,
        cloud_reco_client: CloudRecoService,
    ) -> None:
        """
        It is possible to update a target.
        """
        old_name = uuid.uuid4().hex
        old_width = secrets.choice(seq=range(1, 5000)) / 100
        target_id = vws_client.add_target(
            name=old_name,
            width=old_width,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        [matching_target] = cloud_reco_client.query(image=image)
        assert matching_target.target_id == target_id
        query_target_data = matching_target.target_data
        assert query_target_data is not None
        query_metadata = query_target_data.application_metadata
        assert query_metadata is None

        new_name = uuid.uuid4().hex
        new_width = secrets.choice(seq=range(1, 5000)) / 100
        new_application_metadata = base64.b64encode(s=b"a").decode(
            encoding="ascii",
        )
        vws_client.update_target(
            target_id=target_id,
            name=new_name,
            width=new_width,
            active_flag=True,
            image=different_high_quality_image,
            application_metadata=new_application_metadata,
        )

        vws_client.wait_for_target_processed(target_id=target_id)
        [
            matching_target,
        ] = cloud_reco_client.query(image=different_high_quality_image)
        assert matching_target.target_id == target_id
        query_target_data = matching_target.target_data
        assert query_target_data is not None
        query_metadata = query_target_data.application_metadata
        assert query_metadata == new_application_metadata

        vws_client.update_target(
            target_id=target_id,
            active_flag=False,
        )

        target_details = vws_client.get_target_record(target_id=target_id)
        assert target_details.target_record.name == new_name
        assert target_details.target_record.width == new_width
        assert not target_details.target_record.active_flag

    @staticmethod
    def test_no_fields_given(
        vws_client: VWS,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        It is possible to give no update fields.
        """
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.update_target(target_id=target_id)
