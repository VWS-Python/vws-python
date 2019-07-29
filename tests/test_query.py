"""
Tests for helper functions for managing a Vuforia database.
"""

import io

from vws import VWS, CloudRecoService


class TestQuery:
    """
    Tests for adding a target.
    """

    def test_query(
        self,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        TODO docstring
        """
        result = cloud_reco_client.query(image=high_quality_image)
        assert result == []


# TODO test custom base URL
# TODO test bad credentials
# TODO test no results
# TODO test some results

# TODO do we give an image type? Infer it?
# What happens if we just always give jpeg?
