"""
Tests for helper function for deleting a target from a Vuforia database.
"""

import io

import pytest

from vws import VWS
from vws.exceptions import TargetStatusProcessing, UnknownTarget


class TestDelete:
    """
    Test for deleting a target.
    """

    def test_no_such_target(self, client: VWS) -> None:
        """
        An ``UnknownTarget`` exception is raised if an unknown target is given.
        """
        with pytest.raises(UnknownTarget):
            client.delete_target(target_id='a')

    def test_target_processing(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        XXX
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        with pytest.raises(TargetStatusProcessing):
            client.delete_target(target_id=target_id)

    def test_delete_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """

    def test_delete_target_twice(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
