"""
Tests for the ``CloudRecoService`` querying functionality.
"""

import io
import uuid

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import VWS, CloudRecoService
from vws.exceptions import (
    ConnectionErrorPossiblyImageTooLarge,
    MaxNumResultsOutOfRange,
)
from vws.include_target_data import CloudRecoIncludeTargetData


class TestQuery:
    """
    Tests for making image queries.
    """

    def test_no_matches(
        self,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        An empty list is returned if there are no matches.
        """
        result = cloud_reco_client.query(image=high_quality_image)
        assert result == []

    def test_match(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of matching targets are returned.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        [matching_target] = cloud_reco_client.query(image=high_quality_image)
        assert matching_target.target_id == target_id

    def test_too_large(
        self,
        cloud_reco_client: CloudRecoService,
        png_too_large: io.BytesIO,
    ) -> None:
        """
        A ``ConnectionErrorPossiblyImageTooLarge`` exception is raised if an
        image which is too large is given.
        """
        with pytest.raises(ConnectionErrorPossiblyImageTooLarge):
            cloud_reco_client.query(image=png_too_large)


class TestCustomBaseVWQURL:
    """
    Tests for using a custom base VWQ URL.
    """

    def test_custom_base_url(self, high_quality_image: io.BytesIO) -> None:
        """
        It is possible to use query a target to a database under a custom VWQ
        URL.
        """
        base_vwq_url = 'http://example.com'
        with MockVWS(base_vwq_url=base_vwq_url) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

            vws_client.wait_for_target_processed(target_id=target_id)

            cloud_reco_client = CloudRecoService(
                client_access_key=database.client_access_key,
                client_secret_key=database.client_secret_key,
                base_vwq_url=base_vwq_url,
            )

            matches = cloud_reco_client.query(image=high_quality_image)
            assert len(matches) == 1
            match = matches[0]
            assert match.target_id == target_id


class TestMaxNumResults:
    """
    Tests for the ``max_num_results`` parameter of ``query``.
    """

    def test_default(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        By default the maximum number of results is 1.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        matches = cloud_reco_client.query(image=high_quality_image)
        assert len(matches) == 1

    def test_custom(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to set a custom ``max_num_results``.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_3 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        vws_client.wait_for_target_processed(target_id=target_id_3)
        matches = cloud_reco_client.query(
            image=high_quality_image,
            max_num_results=2,
        )
        assert len(matches) == 2

    def test_too_many(
        self,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        A ``MaxNumResultsOutOfRange`` error is raised if the given
        ``max_num_results`` is out of range.
        """
        with pytest.raises(MaxNumResultsOutOfRange) as exc:
            cloud_reco_client.query(
                image=high_quality_image,
                max_num_results=51,
            )

        expected_value = (
            "Integer out of range (51) in form data part 'max_result'. "
            'Accepted range is from 1 to 50 (inclusive).'
        )
        assert str(exc.value) == exc.value.response.text == expected_value


class TestIncludeTargetData:
    """
    Tests for the ``include_target_data`` parameter of ``query``.
    """

    def test_default(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        By default, target data is only returned in the top match.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=high_quality_image,
            max_num_results=2,
        )
        assert top_match.target_data is not None
        assert second_match.target_data is None

    def test_top(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.TOP`` is given, target data is only
        returned in the top match.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=high_quality_image,
            max_num_results=2,
            include_target_data=CloudRecoIncludeTargetData.TOP,
        )
        assert top_match.target_data is not None
        assert second_match.target_data is None

    def test_none(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.NONE`` is given, target data is not
        returned in any match.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=high_quality_image,
            max_num_results=2,
            include_target_data=CloudRecoIncludeTargetData.NONE,
        )
        assert top_match.target_data is None
        assert second_match.target_data is None

    def test_all(
        self,
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.ALL`` is given, target data is
        returned in all matches.
        """
        target_id = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        target_id_2 = vws_client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=target_id_2)
        top_match, second_match = cloud_reco_client.query(
            image=high_quality_image,
            max_num_results=2,
            include_target_data=CloudRecoIncludeTargetData.ALL,
        )
        assert top_match.target_data is not None
        assert second_match.target_data is not None
