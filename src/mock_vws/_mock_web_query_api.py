"""
A fake implementation of the Vuforia Web Query API.

See
https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
"""

import gzip
import uuid
from typing import Callable, List, Set

from requests_mock import POST
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from mock_vws._constants import ResultCodes
from mock_vws._mock_common import Route, json_dump

ROUTES = set([])


def route(
    path_pattern: str,
    http_methods: List[str],
) -> Callable[..., Callable]:
    """
    Register a decorated method so that it can be recognized as a route.

    Args:
        path_pattern: The end part of a URL pattern. E.g. `/targets` or
            `/targets/.+`.
        http_methods: HTTP methods that map to the route function.
    """

    def decorator(method: Callable[..., str]) -> Callable[..., str]:
        """
        Register a decorated method so that it can be recognized as a route.

        Args:
            method: Method to register.

        Returns:
            The given `method` with multiple changes, including added
            validators.
        """
        ROUTES.add(
            Route(
                route_name=method.__name__,
                path_pattern=path_pattern,
                http_methods=http_methods,
            )
        )

        return method

    return decorator


class MockVuforiaWebQueryAPI:
    """
    A fake implementation of the Vuforia Web Query API.

    This implementation is tied to the implementation of `requests_mock`.
    """

    def __init__(self) -> None:
        """
        Attributes:
            routes: The `Route`s to be used in the mock.
        """
        self.routes: Set[Route] = ROUTES

    @route(path_pattern='/v1/query', http_methods=[POST])
    def query(  # pylint: disable=no-self-use
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,
    ) -> bytes:
        """
        Perform an image recognition query.
        """
        results: List[str] = []
        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'results': results,
            'query_id': uuid.uuid4().hex,
        }

        text = json_dump(body)
        context.headers['Content-Encoding'] = 'gzip'
        value = gzip.compress(text.encode())
        context.headers['Content-Length'] = str(len(value))
        return value
