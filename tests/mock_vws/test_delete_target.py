"""
Tests for deleting targets.
"""

import pytest


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDelete:
    """
    Tests for deleting targets.
    """

    def test_delete(self) -> None:
        """
        It is possible to delete a target.
        """
        pass
