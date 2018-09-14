"""
Tests for helper function for adding a target to a Vuforia database.
"""

import io
import random

import pytest
from mock_vws import MockVWS, States
from PIL import Image
from requests import codes

from vws import VWS
from vws.exceptions import (
    BadImage,
    Fail,
    ImageTooLarge,
    MetadataTooLarge,
    ProjectInactive,
    TargetNameExist,
    UnknownTarget,
)


class TestSuccess:
    """
    Test for successfully adding a target.
    """

    def test_add_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        result = client.get_target(target_id=target_id)
        expected_keys = {
            'target_id',
            'active_flag',
            'name',
            'width',
            'tracking_rating',
            'reco_rating',
        }
        assert result.keys() == expected_keys

    def test_no_such_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding two targets with different names.
        """
        with pytest.raises(UnknownTarget):
            client.get_target(target_id='a')
