"""
Tests for helper functions for managing a Vuforia database.
"""

import io
from typing import Optional

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import CloudRecoService, VWS
from vws.exceptions import TargetProcessingTimeout


class TestQuery:
    """
    Tests for adding a target.
    """

    def test_query(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        cloud_reco_client = CloudRecoService(
            client_access_key='foo',
            client_secret_key='bar',
        )
        result = cloud_reco_client.query(image=high_quality_image)
        # assert result == []

# TODO test custom base URL
# TODO test bad credentials
# TODO test no results
# TODO test some results
# TODO do we give an image type? Infer it? What happens if we just always give jpeg?
