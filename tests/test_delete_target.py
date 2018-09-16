"""
Tests for helper function for deleting a target from a Vuforia database.
"""

import io

from vws import VWS


class TestDelete:
    """
    Test for deleting a target.
    """

    def test_delete_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        it is possible to delete a target.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        client.wait_for_target_processed(target_id=target_id)
        client.delete_target(target_id=target_id)
