"""
Tests for application data in the mock of the update target endpoint.
"""

import base64
import binascii
from typing import Union

import pytest
from requests import codes

from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    VuforiaDatabaseKeys,
    assert_vws_failure,
    assert_vws_response,
    update_target,
    wait_for_target_processed,
)


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestApplicationMetadata:
    """
    Tests for the application metadata parameter.
    """

    def test_base64_encoded(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        A base64 encoded string is valid application metadata.
        """
        metadata = b'Some data'
        metadata_encoded = base64.b64encode(metadata).decode('ascii')

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'application_metadata': metadata_encoded},
            target_id=target_id,
        )

        assert_vws_response(
            response=response,
            status_code=codes.OK,
            result_code=ResultCodes.SUCCESS,
        )

    @pytest.mark.parametrize('invalid_metadata', [1, None])
    def test_invalid_type(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
        invalid_metadata: Union[int, None],
    ) -> None:
        """
        Non-string values cannot be given as valid application metadata.
        """
        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'application_metadata': invalid_metadata},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.BAD_REQUEST,
            result_code=ResultCodes.FAIL,
        )

    def test_not_base64_encoded(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        target_id: str,
    ) -> None:
        """
        A string which is not base64 encoded is not valid application metadata.
        """
        not_base64_encoded = b'a'

        with pytest.raises(binascii.Error):
            base64.b64decode(not_base64_encoded)

        wait_for_target_processed(
            vuforia_database_keys=vuforia_database_keys,
            target_id=target_id,
        )

        response = update_target(
            vuforia_database_keys=vuforia_database_keys,
            data={'application_metadata': str(not_base64_encoded)},
            target_id=target_id,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.UNPROCESSABLE_ENTITY,
            result_code=ResultCodes.FAIL,
        )
