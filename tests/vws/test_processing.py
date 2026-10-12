"""Tests for `VWS` processing."""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Literal

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from tests.image_factory import IMAGE_CASES, ImageFactory
from vws import VWS
from vws.exceptions.custom_exceptions import (
    TargetProcessingTimeoutError,
)
from vws.reports import (
    TargetStatuses,
)

if TYPE_CHECKING:
    import io


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_wait_for_target_processed(
    *,
    vws_client: VWS,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """It is possible to wait until a target is processed."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
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
    vws_client.wait_for_target_processed(target_id=target_id)
    report = vws_client.get_target_summary_report(target_id=target_id)
    assert report.status != TargetStatuses.PROCESSING


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_default_seconds_between_requests(
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """By default, 0.2 seconds are waited between polling requests."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    with MockVWS(processing_time_seconds=0.5) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
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


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_custom_seconds_between_requests(
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """It is possible to customize the time waited between polling
    requests.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    with MockVWS(processing_time_seconds=0.5) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
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


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_custom_timeout(
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
        with pytest.raises(expected_exception=TargetProcessingTimeoutError):
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
