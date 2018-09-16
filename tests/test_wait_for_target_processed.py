"""
Tests for helper function for waiting for a target to be processed.
"""

import io

from vws import VWS


class TestWaitForTargetProcessed:
    """
    Tests for waiting for a target to be processed.
    """

    def test_wait_for_target_processed(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to wait until a target is processed.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )
        report = client.get_target_summary_report(target_id=target_id)
        assert report['status'] == 'processing'
        client.wait_for_target_processed(target_id=target_id)
        report = client.get_target_summary_report(target_id=target_id)
        assert report['status'] != 'processing'
