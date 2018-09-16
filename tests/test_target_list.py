"""
Tests for helper function for getting a list of targets.
"""

import io

from vws import VWS


class TestListTargets:
    """
    Test for listing targets.
    """

    def test_list_targets(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to get a list of target IDs.
        """
        id_1 = client.add_target(name='x', width=1, image=high_quality_image)
        id_2 = client.add_target(name='a', width=1, image=high_quality_image)
        assert sorted(client.list_targets()) == sorted([id_1, id_2])
