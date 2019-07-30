"""
Tests for the ``CloudRecoService`` querying functionality.
"""

import io
import uuid

from vws import VWS, CloudRecoService


class TestQuery:
    """
    Tests for making image queries.
    """

    def test_no_matches(
        self,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        An empty list is returned if there are no matches.
        """
        result = cloud_reco_client.query(image=high_quality_image)
        assert result == []

    def test_match(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of matching targets are returned.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        [matching_target] = cloud_reco_client.query(image=high_quality_image)
        assert matching_target['target_id'] == target_id


class TestMaxNumResults:
    """
    Tests for the ``max_num_results`` parameter of ``query``.
    """

    def test_default(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        By default the maximum number of results is 1.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        matches = cloud_reco_client.query(image=high_quality_image)
        assert len(matches) == 1
