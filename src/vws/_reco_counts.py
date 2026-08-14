"""Internal helpers for the database reco counts report endpoints."""

import json
from http import HTTPStatus

from beartype import BeartypeConf, beartype

from vws.exceptions.custom_exceptions import (
    DatabaseIdNotSetError,
    RecoCountsReportDownloadError,
    RecoCountsReportNotReadyError,
)
from vws.reports import RecoCountsReport
from vws.response import Response  # noqa: TC001


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def reco_counts_report_path(*, database_id: str | None) -> str:
    """Get the path of the reco counts report endpoint for a database.

    Args:
        database_id: The ID of the database to get the path for.

    Returns:
        The path of the reco counts report endpoint.

    Raises:
        ~vws.exceptions.custom_exceptions.DatabaseIdNotSetError: No
            ``database_id`` was given to the client.
    """
    if database_id is None:
        msg = (
            "A database ID is needed to request a reco counts report. Give "
            "``database_id`` when creating the client."
        )
        raise DatabaseIdNotSetError(msg)

    return f"/imagetargets/databases/{database_id}/reports/recoCounts"


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def reco_counts_report_body(*, month: str) -> bytes:
    """Get the request body for requesting a reco counts report.

    Args:
        month: The month to request the report for, in ``YYYY-mm`` form.

    Returns:
        The body of the request.
    """
    return json.dumps(obj={"month": month}).encode(encoding="utf-8")


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def report_from_download_response(*, response: Response) -> RecoCountsReport:
    """Get a reco counts report from a response from a report's URL.

    Args:
        response: The response from a report's download URL.

    Returns:
        The downloaded report.

    Raises:
        ~vws.exceptions.custom_exceptions.RecoCountsReportNotReadyError:
            Vuforia has not finished generating the report.
        ~vws.exceptions.custom_exceptions.RecoCountsReportDownloadError: The
            report could not be downloaded. For example, the report's URL may
            have expired.
    """
    if response.status_code == HTTPStatus.NOT_FOUND:
        raise RecoCountsReportNotReadyError(response=response)

    if response.status_code != HTTPStatus.OK:
        raise RecoCountsReportDownloadError(response=response)

    return RecoCountsReport.from_csv(csv_bytes=response.content)
