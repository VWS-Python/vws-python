"""
A fake implementation of the Vuforia Web Query API.

See
https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
"""

from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

ROUTES = set([])

class MockVuforiaWebQueryAPI:
    """
    XXX
    """

    def __init__(
        self,
    ) -> None:
        """
        XXX
        """

    def query(
        self,
        request: _RequestObjectProxy,
        context: _Context,
    ) -> str:
        """
        XXX
        """
        results = []
        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'results': results,
            'query_id': uuid.uuid4().hex,
        }
        return json.dumps(body)
