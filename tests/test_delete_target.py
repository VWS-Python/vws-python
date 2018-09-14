"""
Tests for helper function for deleting a target from a Vuforia database.
"""

import io

from vws import VWS


class TestDelete:
    """
    Test for deleting a target.
    """

    def test_no_such_target(self, client: VWS) -> None:
        """
        XXX
        """

    def test_target_processing(self, client: VWS) -> None:
        """
        XXX
        """

    def test_delete_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        client.delete_target(target_id='a')

    def test_delete_target_twice(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        client.delete_target(target_id='a')
