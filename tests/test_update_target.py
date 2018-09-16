"""
Tests for helper function for updating a target from a Vuforia database.
"""

import io

import pytest

from vws import VWS
from vws.exceptions import UnknownTarget


class TestUpdateTarget:
    """
    Test for updating a target.
    """

    def test_no_update(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to give ``None`` to each updatable field to update
        nothing.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        client.update_target(
            target_id=target_id,
            name=None,
            width=None,
            image=None,
            active_flag=None,
            application_metadata=None,
        )
