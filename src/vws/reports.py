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
            active_images=int(response_dict["active_images"]),
            current_month_recos=int(response_dict["current_month_recos"]),
            failed_images=int(response_dict["failed_images"]),
            inactive_images=int(response_dict["inactive_images"]),
            name=response_dict["name"],
            previous_month_recos=int(response_dict["previous_month_recos"]),
            processing_images=int(response_dict["processing_images"]),
            reco_threshold=int(response_dict["reco_threshold"]),
            request_quota=int(response_dict["request_quota"]),
            request_usage=int(response_dict["request_usage"]),
            target_quota=int(response_dict["target_quota"]),
            total_recos=int(response_dict["total_recos"]),
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
    def from_response_dict(cls, response_dict: dict[str, Any]) -> Self:
        """Construct from a VWS API response dict."""
        return cls(
            status=TargetStatuses(value=response_dict["status"]),
            database_name=response_dict["database_name"],
            target_name=response_dict["target_name"],
            upload_date=datetime.date.fromisoformat(
                response_dict["upload_date"]
            ),
            active_flag=bool(response_dict["active_flag"]),
            tracking_rating=int(response_dict["tracking_rating"]),
            total_recos=int(response_dict["total_recos"]),
            current_month_recos=int(response_dict["current_month_recos"]),
            previous_month_recos=int(response_dict["previous_month_recos"]),
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
    def from_response_dict(cls, response_dict: dict[str, Any]) -> Self:
        """Construct from a VWS API query result item dict."""
        target_data: TargetData | None = None
        if "target_data" in response_dict:
            target_data_dict = response_dict["target_data"]
            target_timestamp = datetime.datetime.fromtimestamp(
                timestamp=target_data_dict["target_timestamp"],
                tz=datetime.UTC,
            )
            target_data = TargetData(
                name=target_data_dict["name"],
                application_metadata=target_data_dict["application_metadata"],
                target_timestamp=target_timestamp,
            )
        return cls(
            target_id=response_dict["target_id"],
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
    def from_response_dict(cls, response_dict: dict[str, Any]) -> Self:
        """Construct from a VWS API response dict."""
        status = TargetStatuses(value=response_dict["status"])
        target_record_dict = dict(response_dict["target_record"])
        target_record = TargetRecord(
            target_id=target_record_dict["target_id"],
            active_flag=bool(target_record_dict["active_flag"]),
            name=target_record_dict["name"],
            width=float(target_record_dict["width"]),
            tracking_rating=int(target_record_dict["tracking_rating"]),
            reco_rating=target_record_dict["reco_rating"],
        )
        return cls(status=status, target_record=target_record)
