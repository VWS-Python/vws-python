"""
Tests for helper functions for managing a Vuforia database.
"""

import io
import uuid
from requests import codes

import pytest

from vws import VWS, CloudRecoService
from vws.exceptions import AuthenticationFailure, MaxNumResultsOutOfRange


class TestQuery:
    """
    Tests for adding a target.
    """

    def test_no_matches(
        self,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        TODO docstring
        """
        result = cloud_reco_client.query(image=high_quality_image)
        assert result == []

    def test_match(
        self,
        client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        XXX
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )
        client.wait_for_target_processed(target_id=target_id)
        [matching_target] = cloud_reco_client.query(image=high_quality_image)
        assert matching_target['target_id'] == target_id


class TestMaxNumResults:
    """
    Tests for the ``max_num_results`` parameter of ``query``.
    """

    def test_default(
        self,
        client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        XXX
        """
        target_id = client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
        )
        target_id_2 = client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
        )
        client.wait_for_target_processed(target_id=target_id)
        client.wait_for_target_processed(target_id=target_id_2)
        matches = cloud_reco_client.query(image=high_quality_image)
        assert len(matches) == 1

    def test_custom(
        self,
        client: VWS,
        cloud_reco_client: CloudRecoService,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        XXX
        """
        target_id = client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
        )
        target_id_2 = client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
        )
        target_id_3 = client.add_target(
            name=uuid.uuid4().hex,
            width=1,
            image=high_quality_image,
        )
        client.wait_for_target_processed(target_id=target_id)
        client.wait_for_target_processed(target_id=target_id_2)
        client.wait_for_target_processed(target_id=target_id_3)
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
        with pytest.raises(MaxNumResultsOutOfRange) as exc:
            cloud_reco_client.query(
                image=high_quality_image,
                max_num_results=51,
            )

        expected_value = (
            "Integer out of range (51) in form data part 'max_result'. "
            'Accepted range is from 1 to 50 (inclusive).'
        )
        assert str(exc.value) == expected_value

class TestBadCredentials:

    def test_bad_credentials(self, high_quality_image: io.BytesIO):
        cloud_reco_client = CloudRecoService(
            client_access_key='a',
            client_secret_key='a',
        )
        with pytest.raises(AuthenticationFailure) as exc:
            cloud_reco_client.query(image=high_quality_image)

        assert exc.value.response.status_code == codes.UNAUTHORIZED


# TODO test custom base URL
# TODO test options - include_target_data

# TODO do we give an image type? Infer it?
# What happens if we just always give jpeg?
