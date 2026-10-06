"""Tests for `AsyncVWS` reports."""

from __future__ import annotations

import calendar
import time
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, BinaryIO

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from vws import AsyncVWS
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
)
from vws.response import Response

if TYPE_CHECKING:
    import datetime
    import io


class _ForbiddenDownloadTransport:
    """An async transport which refuses to serve a report, as an expired
    URL would.
    """

    async def aclose(self) -> None:
        """Close the transport."""

    async def __call__(
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


@pytest.mark.asyncio
async def test_reco_counts_report(
    *,
    async_vws_client: AsyncVWS,
    report_month: datetime.date,
) -> None:
    """A report can be requested, waited for and downloaded."""
    client = async_vws_client
    report_request = await client.request_database_reco_counts_report(
        year=report_month.year,
        month=calendar.Month(value=report_month.month),
    )
    assert bool(report_request.transaction_id)
    assert bool(report_request.presigned_url)

    report = await client.wait_for_reco_counts_report(
        presigned_url=report_request.presigned_url,
    )

    # No targets have been recognized, so the report has no rows.
    assert not bool(report.reco_counts)
    assert report.raw_csv.startswith(b"target_id,reco_count")


@pytest.mark.asyncio
async def test_not_ready(*, current_month: datetime.date) -> None:
    """Downloading a report before Vuforia has generated it raises an
    error.
    """
    with MockVWS(processing_time_seconds=60) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        async with AsyncVWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            database_id=database.database_id,
        ) as client:
            report_request = await client.request_database_reco_counts_report(
                year=current_month.year,
                month=calendar.Month(value=current_month.month),
            )

            with pytest.raises(
                expected_exception=RecoCountsReportNotReadyError,
            ) as exc:
                await client.download_reco_counts_report(
                    presigned_url=report_request.presigned_url,
                )

            assert exc.value.response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_wait_timeout(*, current_month: datetime.date) -> None:
    """Waiting for a report which is not generated in time raises an
    error.
    """
    with MockVWS(processing_time_seconds=60) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        async with AsyncVWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            database_id=database.database_id,
        ) as client:
            report_request = await client.request_database_reco_counts_report(
                year=current_month.year,
                month=calendar.Month(value=current_month.month),
            )

            maximum_wait_seconds = 5
            start_time = time.monotonic()

            with pytest.raises(
                expected_exception=RecoCountsReportTimeoutError,
            ):
                await client.wait_for_reco_counts_report(
                    presigned_url=report_request.presigned_url,
                    seconds_between_requests=0.01,
                    timeout_seconds=0.05,
                )

            elapsed_time = time.monotonic() - start_time
            assert elapsed_time < maximum_wait_seconds


@pytest.mark.asyncio
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
async def test_month_not_accepted(
    *,
    async_vws_client: AsyncVWS,
    year: int,
    month: calendar.Month,
) -> None:
    """Months other than the current and previous month are
    rejected.
    """
    with pytest.raises(expected_exception=FailError) as exc:
        await async_vws_client.request_database_reco_counts_report(
            year=year,
            month=month,
        )

    assert exc.value.response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_database_id_does_not_match_keys(
    *,
    current_month: datetime.date,
) -> None:
    """A database ID which does not match the given keys is
    rejected.
    """
    with MockVWS() as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        async with AsyncVWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            database_id=uuid.uuid4().hex,
        ) as client:
            with pytest.raises(
                expected_exception=AuthenticationFailureError,
            ) as exc:
                await client.request_database_reco_counts_report(
                    year=current_month.year,
                    month=calendar.Month(value=current_month.month),
                )

            assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_download_error() -> None:
    """An error response from the report's URL raises an error."""
    async with AsyncVWS(
        server_access_key=uuid.uuid4().hex,
        server_secret_key=uuid.uuid4().hex,
        transport=_ForbiddenDownloadTransport(),
    ) as client:
        with pytest.raises(
            expected_exception=RecoCountsReportDownloadError,
        ) as exc:
            await client.download_reco_counts_report(
                presigned_url="https://example.com/reports/recoCounts/x",
            )

        assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_no_database_id(*, current_month: datetime.date) -> None:
    """A client which was given no database ID cannot request a
    report.
    """
    async with AsyncVWS(
        server_access_key=uuid.uuid4().hex,
        server_secret_key=uuid.uuid4().hex,
    ) as client:
        with pytest.raises(expected_exception=DatabaseIdNotSetError):
            await client.request_database_reco_counts_report(
                year=current_month.year,
                month=calendar.Month(value=current_month.month),
            )
