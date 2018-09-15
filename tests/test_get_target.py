"""
Tests for helper function for getting details of a target from a Vuforia
database.
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


class TestGetTarget:
    """
    Test for getting details of a target.
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

        result = client.get_target(target_id=target_id)
        expected_keys = {
            'result_code',
            'transaction_id',
            'target_record',
            'status',
        }
        assert result.keys() == expected_keys

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
