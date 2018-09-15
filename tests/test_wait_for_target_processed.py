"""
Tests for helper function for waiting for a target to be processed.
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
)


class TestWaitForTargetProcessed:
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
        target_details = client.get_target(target_id=target_id)
        assert target_details['status'] == 'processing'
        client.wait_for_target_processed(target_id=target_id)
        target_details = client.get_target(target_id=target_id)
        assert target_details['status'] != 'processing'
