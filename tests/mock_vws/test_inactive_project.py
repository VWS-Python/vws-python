"""
Tests for inactive projects.
"""

import pytest

from tests.utils import VuforiaServerCredentials


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestInactiveProject:
    """
    Tests for inactive projects.
    """

    def test_inactive_project(
        self,
        verify_mock_vuforia_inactive: VuforiaServerCredentials,
    ) -> None:
        """
        X
        """
