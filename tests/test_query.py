"""
Tests for the ``CloudRecoService`` querying functionality.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from vws import VWS, CloudRecoService
from vws.include_target_data import CloudRecoIncludeTargetData

if TYPE_CHECKING:
    import io


class TestQuery:
    """
    Tests for making image queries.
    """

    @staticmethod
    def test_no_matches(
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        An empty list is returned if there are no matches.
        """
        result = cloud_reco_client.query(image=image)
        assert result == []

    @staticmethod
    def test_match(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        Details of matching targets are returned.
        """
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        [matching_target] = cloud_reco_client.query(image=image)
        assert matching_target.target_id == target_id


class TestCustomBaseVWQURL:
    """
    Tests for using a custom base VWQ URL.
    """

    @staticmethod
    def test_custom_base_url(image: io.BytesIO) -> None:
        """
        It is possible to use query a target to a database under a custom VWQ
        URL.
        """
        base_vwq_url = "http://example.com"
        with MockVWS(base_vwq_url=base_vwq_url) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )

            vws_client.wait_for_target_processed(target_id=target_id)

            cloud_reco_client = CloudRecoService(
                client_access_key=database.client_access_key,
                client_secret_key=database.client_secret_key,
                base_vwq_url=base_vwq_url,
            )

            matches = cloud_reco_client.query(image=image)
            assert len(matches) == 1
            match = matches[0]
            assert match.target_id == target_id


class TestMaxNumResults:
    """
    Tests for the ``max_num_results`` parameter of ``query``.
    """

    @staticmethod
    def test_default(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        By default the maximum number of results is 1.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        matches = cloud_reco_client.query(image=image)
        assert len(matches) == 1

    @staticmethod
    def test_custom(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        It is possible to set a custom ``max_num_results``.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_3 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        vws_client.wait_for_target_processed(target_id=target_id_3)
        max_num_results = 2
        matches = cloud_reco_client.query(
            image=image,
            max_num_results=max_num_results,
        )
        assert len(matches) == max_num_results


class TestIncludeTargetData:
    """
    Tests for the ``include_target_data`` parameter of ``query``.
    """

    @staticmethod
    def test_default(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        By default, target data is only returned in the top match.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=image,
            max_num_results=2,
        )
        assert top_match.target_data is not None
        assert second_match.target_data is None

    @staticmethod
    def test_top(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.TOP`` is given, target data is only
        returned in the top match.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=image,
            max_num_results=2,
            include_target_data=CloudRecoIncludeTargetData.TOP,
        )
        assert top_match.target_data is not None
        assert second_match.target_data is None

    @staticmethod
    def test_none(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.NONE`` is given, target data is not
        returned in any match.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=image,
            max_num_results=2,
            include_target_data=CloudRecoIncludeTargetData.NONE,
        )
        assert top_match.target_data is None
        assert second_match.target_data is None

    @staticmethod
    def test_all(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.ALL`` is given, target data is
        returned in all matches.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=image,
            max_num_results=2,
            include_target_data=CloudRecoIncludeTargetData.ALL,
        )
        assert top_match.target_data is not None
        assert second_match.target_data is not None
