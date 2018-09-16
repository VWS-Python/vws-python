"""
Tests for helper function for getting a summary report for a target in a
Vuforia database.
"""

import io

from vws import VWS


class TestGetTargetSummaryReport:
    """
    Tests for getting a summary report for a target.
    """

    def test_get_target_summary_report(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_summary_report``.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        result = client.get_target_summary_report(target_id=target_id)
        expected_keys = {
            'status',
            'result_code',
            'transaction_id',
            'database_name',
            'target_name',
            'upload_date',
            'active_flag',
            'tracking_rating',
            'total_recos',
            'current_month_recos',
            'previous_month_recos',
        }
        assert result.keys() == expected_keys
