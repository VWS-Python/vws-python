"""
Tests for helper functions for managing a Vuforia database.
"""

import io

from vws import VWS, CloudRecoService


class TestQuery:
    """
    Tests for adding a target.
    """

    def test_no_matches(
        self,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        TODO docstring
        """
        result = cloud_reco_client.query(image=high_quality_image)
        assert result == []

    def test_match(
        self,
        client: VWS,
        cloud_reco_client: CloudRecoService,
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
        client.wait_for_target_processed(target_id=target_id)
        [matching_target] = cloud_reco_client.query(image=high_quality_image)
        assert matching_target['target_id'] == target_id


# TODO test custom base URL
# TODO test bad credentials
# TODO test options - max_num_results + include_target_data

# TODO do we give an image type? Infer it?
# What happens if we just always give jpeg?
