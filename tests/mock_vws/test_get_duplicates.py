"""
Tests for the mock of the get duplicates endpoint.
"""

@pytest.mark.usefixtures('verify_mock_vuforia')
class TestDuplicates:
    """
    Tests for the mock of the target duplicates endpoint.
    """

    def test_no_duplicates(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        target_id: str,
    ):
        """
        XXX
        """
        pass
