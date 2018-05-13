"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

import pytest
import requests

from tests.mock_vws.utils import Endpoint, assert_query_success


@pytest.mark.usefixtures('verify_mock_vuforia')
class TestQuery:
    """
    Tests for the query endpoint.
    """

    def test_no_results(
        self,
        query_endpoint: Endpoint,
    ) -> None:
        """
        When there are no matching images in the database, an empty list of
        results is returned.
        """
        session = requests.Session()
        response = session.send(  # type: ignore
            request=query_endpoint.prepared_request,
        )
        assert_query_success(response=response)
        assert response.json()['results'] == []
