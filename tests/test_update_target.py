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

    def test_get_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target``.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        client.update_target(target_id=target_id)
        result = client.get_target(target_id=target_id)
        expected_keys = {
            'target_id',
            'active_flag',
            'name',
            'width',
            'tracking_rating',
            'reco_rating',
        }
        assert result['target_record'].keys() == expected_keys

    def test_no_such_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        An ``UnknownTarget`` exception is raised when getting a target which
        does not exist.
        """
        with pytest.raises(UnknownTarget):
            client.get_target(target_id='a')
