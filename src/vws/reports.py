"""
Classes for representing Vuforia reports.
"""

from dataclasses import dataclass


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
