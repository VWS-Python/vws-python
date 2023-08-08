"""
Classes for representing Vuforia reports.
"""

import datetime
from dataclasses import dataclass
from enum import Enum


@dataclass
class DatabaseSummaryReport:
    """
    A database summary report.

    See
    https://library.vuforia.com/web-api/cloud-targets-web-services-api#summary-report.
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


class TargetStatuses(Enum):
    """Constants representing VWS target statuses.

    See the 'status' field in
    https://library.vuforia.com/web-api/cloud-targets-web-services-api#target-record
    """

    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TargetSummaryReport:
    """
    A target summary report.

    See
    https://library.vuforia.com/web-api/cloud-targets-web-services-api#summary-report.
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


@dataclass
class TargetRecord:
    """
    A target record.

    See
    https://library.vuforia.com/web-api/cloud-targets-web-services-api#target-record.
    """

    target_id: str
    active_flag: bool
    name: str
    width: float
    tracking_rating: int
    reco_rating: str


@dataclass
class TargetData:
    """
    The target data optionally included with a query match.
    """

    name: str
    application_metadata: str | None
    target_timestamp: datetime.datetime


@dataclass
class QueryResult:
    """
    One query match result.

    See
    https://library.vuforia.com/web-api/vuforia-query-web-api.
    """

    target_id: str
    target_data: TargetData | None


@dataclass
class TargetStatusAndRecord:
    """
    The target status and a target record.

    See
    https://library.vuforia.com/web-api/cloud-targets-web-services-api#target-record.
    """

    status: TargetStatuses
    target_record: TargetRecord
