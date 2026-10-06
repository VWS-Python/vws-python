"""Tests for `VWS` reports."""

from __future__ import annotations

import calendar
import datetime
import time
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, BinaryIO

import pytest
from freezegun import freeze_time
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from vws import VWS
from vws.exceptions.custom_exceptions import (
    DatabaseIdNotSetError,
    RecoCountsReportDownloadError,
    RecoCountsReportNotReadyError,
    RecoCountsReportTimeoutError,
)
from vws.exceptions.vws_exceptions import (
    AuthenticationFailureError,
    FailError,
)
from vws.reports import (
    DatabaseSummaryReport,
    RecoCount,
    RecoCountsReport,
    TargetStatuses,
    TargetSummaryReport,
)
from vws.response import Response

if TYPE_CHECKING:
    import io


class _ForbiddenDownloadTransport:
    """A transport which refuses to serve a report, as an expired URL
    would.
    """

    def close(self) -> None:
        """Close the transport."""

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Return a "forbidden" response."""
        del method, headers, request_timeout
        body = "<Error><Code>AccessDenied</Code></Error>"
        return Response(
            text=body,
            url=url,
            status_code=HTTPStatus.FORBIDDEN,
            headers={},
            request_body=data,
            tell_position=0,
            content=body.encode(encoding="utf-8"),
        )


def test_get_target_summary_report(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """Details of a target are returned by
    ``get_target_summary_report``.
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
    assert report.current_month_recos == expected_report.current_month_recos
    assert report.previous_month_recos == expected_report.previous_month_recos

    assert report == expected_report


def test_get_target(vws_client: VWS) -> None:
    """Details of a database are returned by
    ``get_database_summary_report``.
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
    assert report.current_month_recos == expected_report.current_month_recos
    assert report.failed_images == expected_report.failed_images
    assert report.inactive_images == expected_report.inactive_images
    assert report.name == expected_report.name
    assert report.previous_month_recos == expected_report.previous_month_recos
    assert report.processing_images == expected_report.processing_images
    assert report.reco_threshold == expected_report.reco_threshold
    assert report.request_quota == expected_report.request_quota
    assert report.request_usage == expected_report.request_usage
    assert report.target_quota == expected_report.target_quota
    assert report.total_recos == expected_report.total_recos

    assert report == expected_report


def test_reco_counts_report(
    *,
    vws_client: VWS,
    report_month: datetime.date,
) -> None:
    """A report can be requested, waited for and downloaded."""
    report_request = vws_client.request_database_reco_counts_report(
        year=report_month.year,
        month=calendar.Month(value=report_month.month),
    )
    assert bool(report_request.transaction_id)
    assert bool(report_request.presigned_url)

    report = vws_client.wait_for_reco_counts_report(
        presigned_url=report_request.presigned_url,
    )

    # No targets have been recognized, so the report has no rows.
    assert not bool(report.reco_counts)
    assert report.raw_csv.startswith(b"target_id,reco_count")


def test_not_ready(*, current_month: datetime.date) -> None:
    """Downloading a report before Vuforia has generated it raises an
    error.
    """
    with MockVWS(processing_time_seconds=60) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            database_id=database.database_id,
        )
        report_request = vws_client.request_database_reco_counts_report(
            year=current_month.year,
            month=calendar.Month(value=current_month.month),
        )

        with pytest.raises(
            expected_exception=RecoCountsReportNotReadyError,
        ) as exc:
            _ = vws_client.download_reco_counts_report(
                presigned_url=report_request.presigned_url,
            )

    assert exc.value.response.status_code == HTTPStatus.NOT_FOUND


def test_wait_timeout(*, current_month: datetime.date) -> None:
    """Waiting for a report which is not generated in time raises an
    error.
    """
    with MockVWS(processing_time_seconds=60) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            database_id=database.database_id,
        )
        report_request = vws_client.request_database_reco_counts_report(
            year=current_month.year,
            month=calendar.Month(value=current_month.month),
        )

        maximum_wait_seconds = 5
        start_time = time.monotonic()

        with pytest.raises(
            expected_exception=RecoCountsReportTimeoutError,
        ):
            _ = vws_client.wait_for_reco_counts_report(
                presigned_url=report_request.presigned_url,
                seconds_between_requests=0.01,
                timeout_seconds=0.05,
            )

        elapsed_time = time.monotonic() - start_time
        assert elapsed_time < maximum_wait_seconds


@pytest.mark.parametrize(
    argnames=("year", "month"),
    argvalues=[
        pytest.param(1999, calendar.Month.JANUARY, id="year-in-the-past"),
        pytest.param(
            1999,
            calendar.Month.DECEMBER,
            id="year-in-the-past-december",
        ),
    ],
)
def test_month_not_accepted(
    *,
    vws_client: VWS,
    year: int,
    month: calendar.Month,
) -> None:
    """Months other than the current and previous month are
    rejected.
    """
    with pytest.raises(expected_exception=FailError) as exc:
        _ = vws_client.request_database_reco_counts_report(
            year=year,
            month=month,
        )

    assert exc.value.response.status_code == HTTPStatus.BAD_REQUEST


def test_database_id_does_not_match_keys(
    *,
    current_month: datetime.date,
) -> None:
    """A database ID which does not match the given keys is
    rejected.
    """
    with MockVWS() as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            database_id=uuid.uuid4().hex,
        )

        with pytest.raises(
            expected_exception=AuthenticationFailureError,
        ) as exc:
            _ = vws_client.request_database_reco_counts_report(
                year=current_month.year,
                month=calendar.Month(value=current_month.month),
            )

    assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED


def test_download_error() -> None:
    """An error response from the report's URL raises an error."""
    vws_client = VWS(
        server_access_key=uuid.uuid4().hex,
        server_secret_key=uuid.uuid4().hex,
        transport=_ForbiddenDownloadTransport(),
    )

    with pytest.raises(
        expected_exception=RecoCountsReportDownloadError,
    ) as exc:
        _ = vws_client.download_reco_counts_report(
            presigned_url="https://example.com/reports/recoCounts/x",
        )

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


def test_no_database_id(*, current_month: datetime.date) -> None:
    """A client which was given no database ID cannot request a
    report.
    """
    vws_client = VWS(
        server_access_key=uuid.uuid4().hex,
        server_secret_key=uuid.uuid4().hex,
    )

    with pytest.raises(expected_exception=DatabaseIdNotSetError):
        _ = vws_client.request_database_reco_counts_report(
            year=current_month.year,
            month=calendar.Month(value=current_month.month),
        )


def test_rows() -> None:
    """Each row of the CSV becomes a ``RecoCount``."""
    csv_bytes = b"target_id,reco_count\r\nabc,3\r\ndef,0\r\n"

    report = RecoCountsReport.from_csv(csv_bytes=csv_bytes)

    assert report.reco_counts == [
        RecoCount(target_id="abc", reco_count=3),
        RecoCount(target_id="def", reco_count=0),
    ]
    assert report.raw_csv == csv_bytes


def test_unknown_columns_ignored() -> None:
    """Columns which are not known are not exposed in
    ``reco_counts``.
    """
    expected_reco_count = 3
    header = "target_id,reco_count,new_column\r\n"
    csv_text = f"{header}abc,{expected_reco_count},x\r\n"

    report = RecoCountsReport.from_csv(
        csv_bytes=csv_text.encode(encoding="utf-8"),
    )

    (item,) = report.reco_counts
    assert item.target_id == "abc"
    assert item.reco_count == expected_reco_count
