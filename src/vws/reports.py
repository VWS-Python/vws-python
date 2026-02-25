"""Classes for representing Vuforia reports."""

import datetime
from dataclasses import dataclass
from enum import Enum, unique
from typing import Any, Self

from beartype import BeartypeConf, beartype


@beartype
@dataclass(frozen=True)
class DatabaseSummaryReport:
    """A database summary report.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#summary-report.
    """

    active_images: int
    current_month_recos: int
    failed_images: int
    inactive_images: int
    name: str
    previous_month_recos: int
    processing_images: int
    reco_threshold: int
    request_quota: int
    request_usage: int
    target_quota: int
    total_recos: int

    @classmethod
    def from_response_dict(cls, response_dict: dict[str, Any]) -> Self:
        """Construct from a VWS API response dict."""
        return cls(
            active_images=int(response_dict["active_images"]),  # type: ignore[arg-type]
            current_month_recos=int(response_dict["current_month_recos"]),  # type: ignore[arg-type]
            failed_images=int(response_dict["failed_images"]),  # type: ignore[arg-type]
            inactive_images=int(response_dict["inactive_images"]),  # type: ignore[arg-type]
            name=response_dict["name"],  # type: ignore[arg-type]
            previous_month_recos=int(response_dict["previous_month_recos"]),  # type: ignore[arg-type]
            processing_images=int(response_dict["processing_images"]),  # type: ignore[arg-type]
            reco_threshold=int(response_dict["reco_threshold"]),  # type: ignore[arg-type]
            request_quota=int(response_dict["request_quota"]),  # type: ignore[arg-type]
            request_usage=int(response_dict["request_usage"]),  # type: ignore[arg-type]
            target_quota=int(response_dict["target_quota"]),  # type: ignore[arg-type]
            total_recos=int(response_dict["total_recos"]),  # type: ignore[arg-type]
        )


@beartype
@unique
class TargetStatuses(Enum):
    """Constants representing VWS target statuses.

    See the 'status' field in
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#target-record
    """

    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


@beartype
@dataclass(frozen=True)
class TargetSummaryReport:
    """A target summary report.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#summary-report.
    """

    status: TargetStatuses
    database_name: str
    target_name: str
    upload_date: datetime.date
    active_flag: bool
    tracking_rating: int
    total_recos: int
    current_month_recos: int
    previous_month_recos: int

    @classmethod
    def from_response_dict(cls, response_dict: dict[str, Any]) -> Self:  # type: ignore[name-defined]
        """Construct from a VWS API response dict."""
        return cls(  # type: ignore[arg-type]
            status=TargetStatuses(value=response_dict["status"]),  # type: ignore[arg-type]
            database_name=response_dict["database_name"],  # type: ignore[arg-type]
            target_name=response_dict["target_name"],  # type: ignore[arg-type]
            upload_date=datetime.date.fromisoformat(
                response_dict["upload_date"]
            ),  # type: ignore[arg-type]
            active_flag=bool(response_dict["active_flag"]),  # type: ignore[arg-type]
            tracking_rating=int(response_dict["tracking_rating"]),  # type: ignore[arg-type]
            total_recos=int(response_dict["total_recos"]),  # type: ignore[arg-type]
            current_month_recos=int(response_dict["current_month_recos"]),  # type: ignore[arg-type]
            previous_month_recos=int(response_dict["previous_month_recos"]),  # type: ignore[arg-type]
        )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
@dataclass(frozen=True)
class TargetRecord:
    """A target record.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#target-record.
    """

    target_id: str
    active_flag: bool
    name: str
    width: float
    tracking_rating: int
    reco_rating: str


@beartype
@dataclass(frozen=True)
class TargetData:
    """The target data optionally included with a query match."""

    name: str
    application_metadata: str | None
    target_timestamp: datetime.datetime


@beartype
@dataclass(frozen=True)
class QueryResult:
    """One query match result.

    See
    https://developer.vuforia.com/library/web-api/vuforia-query-web-api.
    """

    target_id: str
    target_data: TargetData | None

    @classmethod
    def from_response_dict(cls, response_dict: dict[str, Any]) -> Self:  # type: ignore[name-defined]
        """Construct from a VWS API query result item dict."""
        target_data: TargetData | None = None
        if "target_data" in response_dict:
            target_data_dict = response_dict["target_data"]
            target_timestamp = datetime.datetime.fromtimestamp(
                timestamp=target_data_dict["target_timestamp"],  # type: ignore[arg-type]
                tz=datetime.UTC,
            )
            target_data = TargetData(
                name=target_data_dict["name"],  # type: ignore[arg-type]
                application_metadata=target_data_dict["application_metadata"],  # type: ignore[arg-type]
                target_timestamp=target_timestamp,
            )
        return cls(  # type: ignore[arg-type]
            target_id=response_dict["target_id"],  # type: ignore[arg-type]
            target_data=target_data,
        )


@beartype
@dataclass(frozen=True)
class TargetStatusAndRecord:
    """The target status and a target record.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#target-record.
    """

    status: TargetStatuses
    target_record: TargetRecord

    @classmethod
    def from_response_dict(cls, response_dict: dict[str, Any]) -> Self:  # type: ignore[name-defined]
        """Construct from a VWS API response dict."""
        status = TargetStatuses(value=response_dict["status"])  # type: ignore[arg-type]
        target_record_dict = dict(response_dict["target_record"])
        target_record = TargetRecord(
            target_id=target_record_dict["target_id"],  # type: ignore[arg-type]
            active_flag=bool(target_record_dict["active_flag"]),  # type: ignore[arg-type]
            name=target_record_dict["name"],  # type: ignore[arg-type]
            width=float(target_record_dict["width"]),  # type: ignore[arg-type]
            tracking_rating=int(target_record_dict["tracking_rating"]),  # type: ignore[arg-type]
            reco_rating=target_record_dict["reco_rating"],  # type: ignore[arg-type]
        )
        return cls(status=status, target_record=target_record)  # type: ignore[arg-type]
