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
        No exception is raised when adding one target.
        """
