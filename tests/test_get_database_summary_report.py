"""
Tests for helper function for getting a summary report for a Vuforia database.
"""

import io

from vws import VWS


class TestGetDatabaseSummaryReport:
    """
    Tests for getting a summary report for a database.
    """

    def test_get_target(self, client: VWS) -> None:
        """
        Details of a database are returned by ``get_database_summary_report``.
        """
        report = client.get_database_summary_report()
        expected_keys = {
            'active_images',
            'current_month_recos',
            'failed_images',
            'inactive_images',
            'name',
            'previous_month_recos',
            'processing_images',
            'reco_threshold',
            'request_quota',
            'request_usage',
            'result_code',
            'target_quota',
            'total_recos',
            'transaction_id',
        }
        assert report.keys() == expected_keys
