import base64
import io
import uuid
from time import sleep

import pytest
import requests
import timeout_decorator
from requests import codes
from requests.structures import CaseInsensitiveDict

from mock_vws import MockVWS
from mock_vws._constants import ResultCodes
from tests.mock_vws.utils import (
    Endpoint,
    add_target_to_vws,
    database_summary,
    delete_target,
    query,
    wait_for_target_processed,
)
from tests.mock_vws.utils.assertions import assert_vws_response
from tests.mock_vws.utils.authorization import (
    VuforiaDatabaseKeys,
    authorization_header,
    rfc_1123_date,
)


@pytest.mark.usefixtures('verify_mock_vuforia_inactive')
class TestInactiveProject:
    """
    Tests for inactive projects.
    """

    def test_inactive_project(
        self,
        inactive_database_keys: VuforiaDatabaseKeys,
        vuforia_database_keys: VuforiaDatabaseKeys,
        endpoint_success_no_target_id: Endpoint,
    ) -> None:
        """
        The project's active state does not affect the database summary.
        """
        endpoint = endpoint_success_no_target_id
        endpoint_headers = dict(endpoint.prepared_request.headers)
        content = endpoint.prepared_request.body or b''
        if 'query' in endpoint.prepared_request.url:
            # TODO fix this up for query
            return
        assert isinstance(content, bytes)
        date = rfc_1123_date()

        keys = inactive_database_keys
        # keys = vuforia_database_keys

        authorization_string = authorization_header(
            access_key=keys.server_access_key,
            secret_key=keys.server_secret_key,
            method=str(endpoint.prepared_request.method),
            content=content,
            content_type=endpoint.auth_header_content_type,
            date=date,
            request_path=endpoint.prepared_request.path_url,
        )

        headers = {
            **endpoint_headers,
            'Authorization': authorization_string,
            'Date': date,
        }

        endpoint.prepared_request.headers = CaseInsensitiveDict(data=headers)
        session = requests.Session()
        response = session.send(  # type: ignore
            request=endpoint.prepared_request,
        )

        assert_vws_response(
            response=response,
            status_code=endpoint.successful_headers_status_code,
            result_code=endpoint.successful_headers_result_code,
        )
