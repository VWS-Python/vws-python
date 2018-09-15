"""
Tests for helper function for adding a target to a Vuforia database.
"""

import io

from mock_vws import MockVWS

from vws import VWS


class TestSuccess:
    """
    Tests for successfully adding a target.
    """

    def test_add_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        client.add_target(name='x', width=1, image=high_quality_image)

    def test_add_two_targets(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding two targets with different names.
        """
        client.add_target(name='x', width=1, image=high_quality_image)
        client.add_target(name='a', width=1, image=high_quality_image)


class TestCustomBaseURL:
    """
    Tests for adding images to databases under custom VWS URLs.
    """

    def test_custom_base_url(self, high_quality_image: io.BytesIO) -> None:
        """
        It is possible to use add a target to a database under a custom VWS
        URL.
        """
        base_vws_url = 'http://example.com'
        with MockVWS(base_vws_url=base_vws_url) as mock:
            client = VWS(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
                base_vws_url=base_vws_url,
            )

            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )
