"""
Tests for helper function for adding a target to a Vuforia database.
"""

import io
from typing import Optional

import pytest
from mock_vws import MockVWS

from vws import VWS
from vws.exceptions import UnknownTarget


class TestAddTarget:
    """
    Tests for adding a target.
    """

    def test_add_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        name = 'x'
        width = 1
        target_id = client.add_target(
            name=name,
            width=width,
            image=high_quality_image,
        )
        target_record = client.get_target_record(target_id=target_id)
        assert target_record['name'] == name
        assert target_record['width'] == width
        assert target_record['active_flag'] is True

    def test_add_two_targets(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding two targets with different names.

        This demonstrates that the image seek position is not changed.
        """
        client.add_target(name='x', width=1, image=high_quality_image)
        client.add_target(name='a', width=1, image=high_quality_image)

    @pytest.mark.parametrize('application_metadata', [None, b'a'])
    def test_valid_metadata(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
        application_metadata: Optional[bytes],
    ) -> None:
        """
        No exception is raised when ``None`` or bytes is given.
        """
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=application_metadata,
        )

    @pytest.mark.parametrize('active_flag', [True, False])
    def test_active_flag_given(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
        active_flag: bool,
    ) -> None:
        """
        It is possible to set the active flag to a boolean value.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=active_flag,
        )
        target_record = client.get_target_record(target_id=target_id)
        assert target_record['active_flag'] is active_flag


class TestCustomBaseVWSURL:
    """
    Tests for using a custom base VWS URL.
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


class TestListTargets:
    """
    Tests for listing targets.
    """

    def test_list_targets(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to get a list of target IDs.
        """
        id_1 = client.add_target(name='x', width=1, image=high_quality_image)
        id_2 = client.add_target(name='a', width=1, image=high_quality_image)
        assert sorted(client.list_targets()) == sorted([id_1, id_2])


class TestDelete:
    """
    Test for deleting a target.
    """

    def test_delete_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to delete a target.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        client.wait_for_target_processed(target_id=target_id)
        client.delete_target(target_id=target_id)
        with pytest.raises(UnknownTarget):
            client.get_target_record(target_id=target_id)
