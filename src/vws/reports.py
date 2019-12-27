"""
Classes for representing Vuforia reports.
"""

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class DatabaseSummaryReport:
    """
    A database summary report.

    See
    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Get-a-Database-Summary-Report.
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
    """
    Constants representing VWS target statuses.
    See the 'status' field in
    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Retrieve-a-Target-Record
    """

    PROCESSING = 'processing'
    SUCCESS = 'success'
    FAILED = 'failed'


@dataclass
class TargetSummaryReport:
    """
    A target summary report.

    See
    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Retrieve-a-Target-Summary-Report.
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
    A target summary record.

    See
    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Retrieve-a-Target-Record.
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
    application_metadata: Optional[str]
    target_timestamp: datetime.datetime


@dataclass
class QueryResult:
    """
    One query match result.

    See
    https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
    """

    target_id: str
    target_data: Optional[TargetData]
