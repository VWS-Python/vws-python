"""
Classes for representing Vuforia reports.
"""

import datetime
from dataclasses import dataclass
from enum import Enum, unique

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
    """
    The target data optionally included with a query match.
    """

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


@beartype
@dataclass(frozen=True)
class TargetStatusAndRecord:
    """The target status and a target record.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#target-record.
    """

    status: TargetStatuses
    target_record: TargetRecord
