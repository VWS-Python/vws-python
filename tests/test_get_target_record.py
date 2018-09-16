"""
Tests for helper function for getting a record of a target from a Vuforia
database.
"""

import io

from vws import VWS


class TestGetTargetRecord:
    """
    Tests for getting a record of a target.
    """

    def test_get_target_record(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_record``.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        result = client.get_target_record(target_id=target_id)

        expected_keys = {
            'target_id',
            'active_flag',
            'name',
            'width',
            'tracking_rating',
            'reco_rating',
        }
        assert result.keys() == expected_keys
