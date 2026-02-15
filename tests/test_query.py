"""Tests for the ``CloudRecoService`` querying functionality."""

import datetime
import io
import uuid
from typing import BinaryIO

import pytest
import requests
from freezegun import freeze_time
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import VWS, CloudRecoService
from vws.include_target_data import CloudRecoIncludeTargetData


class TestQuery:
    """Tests for making image queries."""

    @staticmethod
    def test_no_matches(
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """An empty list is returned if there are no matches."""
        result = cloud_reco_client.query(image=image)
        assert result == []

    @staticmethod
    def test_match(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """Details of matching targets are returned."""
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


class TestCustomRequestTimeout:
    """Tests for using a custom request timeout."""

    @staticmethod
    @pytest.mark.parametrize(
        argnames=("response_delay_seconds", "expect_timeout"),
        argvalues=[(29, False), (31, True)],
    )
    def test_default_timeout(
        image: io.BytesIO | BinaryIO,
        *,
        response_delay_seconds: int,
        expect_timeout: bool,
    ) -> None:
        """At 29 seconds there is no error; at 31 seconds there is a
        timeout.
        """
        with (
            freeze_time() as frozen_datetime,
            MockVWS(
                response_delay_seconds=response_delay_seconds,
                sleep_fn=lambda seconds: (
                    frozen_datetime.tick(
                        delta=datetime.timedelta(seconds=seconds),
                    ),
                    None,
                )[1],
            ) as mock,
        ):
            database = VuforiaDatabase()
            mock.add_database(database=database)
            cloud_reco_client = CloudRecoService(
                client_access_key=database.client_access_key,
                client_secret_key=database.client_secret_key,
            )

            if expect_timeout:
                with pytest.raises(
                    expected_exception=requests.exceptions.Timeout,
                ):
                    cloud_reco_client.query(image=image)
            else:
                matches = cloud_reco_client.query(image=image)
                assert not matches

    @staticmethod
    def test_timeout_raises_on_slow_response(
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """A short timeout raises an error when the server is slow."""
        with MockVWS(response_delay_seconds=0.5) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )
            cloud_reco_client = CloudRecoService(
                client_access_key=database.client_access_key,
                client_secret_key=database.client_secret_key,
                request_timeout_seconds=0.1,
            )

            target_id = vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )
            vws_client.wait_for_target_processed(target_id=target_id)

            with pytest.raises(expected_exception=requests.exceptions.Timeout):
                cloud_reco_client.query(image=image)


class TestCustomBaseVWQURL:
    """Tests for using a custom base VWQ URL."""

    @staticmethod
    def test_custom_base_url(image: io.BytesIO | BinaryIO) -> None:
        """
        It is possible to use query a target to a database under a
        custom
        VWQ
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
    """Tests for the ``max_num_results`` parameter of ``query``."""

    @staticmethod
    def test_default(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """By default the maximum number of results is 1."""
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
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """It is possible to set a custom ``max_num_results``."""
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
    """Tests for the ``include_target_data`` parameter of ``query``."""

    @staticmethod
    def test_default(
        vws_client: VWS,
        cloud_reco_client: CloudRecoService,
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """By default, target data is only returned in the top match."""
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
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.TOP`` is given, target data is
        only
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
        image: io.BytesIO | BinaryIO,
    ) -> None:
        """
        When ``CloudRecoIncludeTargetData.NONE`` is given, target data
        is
        not
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
        image: io.BytesIO | BinaryIO,
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
