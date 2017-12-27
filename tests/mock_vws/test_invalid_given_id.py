"""
Tests for passing invalid endpoints which require a target ID to be given.
"""

import pytest
import requests
from requests import codes

from common.constants import ResultCodes
from tests.mock_vws.utils import Endpoint, assert_vws_failure
from tests.utils import VuforiaDatabaseKeys
from vws._request_utils import authorization_header, rfc_1123_date


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestInvalidGivenID:
    """
    Tests for giving an invalid ID to endpoints which require a target ID to
    be given.
    """

    def test_not_real_id(
        self,
        vuforia_database_keys: VuforiaDatabaseKeys,
        endpoint_which_takes_target_id: Endpoint,  # noqa: E501 pylint: disable=redefined-outer-name
    ) -> None:
        """
        A `NOT_FOUND` error is returned when an endpoint is given a target ID
        of a target which does not exist.
        """
        endpoint = endpoint_which_takes_target_id
        request_path = endpoint.example_path
        date = rfc_1123_date()

        authorization_string = authorization_header(
            server_access_key=vuforia_database_keys.server_access_key,
            server_secret_key=vuforia_database_keys.server_secret_key,
            method=endpoint.method,
            content=endpoint.content,
            content_type=endpoint.content_type or '',
            date=date,
            request_path=request_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
        }
        if endpoint.content_type is not None:
            headers['Content-Type'] = endpoint.content_type

        response = requests.request(
            method=endpoint.method,
            url=endpoint.url,
            headers=headers,
            data=endpoint.content,
        )

        assert_vws_failure(
            response=response,
            status_code=codes.NOT_FOUND,
            result_code=ResultCodes.UNKNOWN_TARGET,
        )
