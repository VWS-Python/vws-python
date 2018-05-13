"""
A fake implementation of the Vuforia Web Query API.

See
https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
"""

import cgi
import io
import uuid
from typing import Callable, List, Set

from requests import codes
from requests_mock import POST
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from mock_vws._constants import ResultCodes
from mock_vws._mock_common import Route, json_dump, set_content_length_header

from ._validators import (
    validate_auth_header_exists,
    validate_authorization,
    validate_date,
    validate_not_invalid_json,
)

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
            ),
        )

        decorators = [
            validate_authorization,
            validate_date,
            validate_not_invalid_json,
            validate_auth_header_exists,
            set_content_length_header,
        ]

        for decorator in decorators:
            method = decorator(method)

        return method

    return decorator


class MockVuforiaWebQueryAPI:
    """
    A fake implementation of the Vuforia Web Query API.

    This implementation is tied to the implementation of `requests_mock`.
    """

    def __init__(
        self,
        client_access_key: str,
        client_secret_key: str,
    ) -> None:
        """
        Args:
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.

        Attributes:
            routes: The `Route`s to be used in the mock.
            access_key (str): A VWS client access key.
            secret_key (str): A VWS client secret key.
        """
        self.routes: Set[Route] = ROUTES
        self.access_key: str = client_access_key
        self.secret_key: str = client_secret_key

    @route(path_pattern='/v1/query', http_methods=[POST])
    def query(
        self,
        request: _RequestObjectProxy,
        context: _Context,
    ) -> str:
        """
        Perform an image recognition query.
        """
        body_file = io.BytesIO(request.body)

        _, pdict = cgi.parse_header(request.headers['Content-Type'])
        parsed = cgi.parse_multipart(
            fp=body_file,
            pdict={
                'boundary': pdict['boundary'].encode(),
            },
        )

        [max_num_results] = parsed.get('max_num_results', [b'1'])
        try:
            max_num_results = int(max_num_results)
        except ValueError:
            try:
                max_num_results = max_num_results.decode()
            except AttributeError:
                pass

            context.status_code = codes.BAD_REQUEST
            invalid_type_error = (
                f"Invalid value '{max_num_results}' in form data part "
                "'max_result'. "
                'Expecting integer value in range from 1 to 50 (inclusive).'
            )
            return invalid_type_error

        if max_num_results < 1 or max_num_results > 50:
            context.status_code = codes.BAD_REQUEST
            out_of_range_error = (
                f'Integer out of range ({max_num_results}) in form data part '
                "'max_result'. Accepted range is from 1 to 50 (inclusive)."
            )
            return out_of_range_error

        results: List[str] = []
        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'results': results,
            'query_id': uuid.uuid4().hex,
        }

        value = json_dump(body)
        return value
