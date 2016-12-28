"""
A fake implementation of VWS.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Union  # noqa F401
from typing import Callable, Dict, List, Tuple

import wrapt
from requests import codes
from requests_mock import GET
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from common.constants import ResultCodes
from vws._request_utils import authorization_header


@wrapt.decorator
def validate_authorization(wrapped: Callable[..., str],
                           instance: 'MockVuforiaTargetAPI',
                           args: Tuple,
                           kwargs: Dict) -> str:
    """
    Validate the authorization header given to a VWS endpoint.

    Args:
        wrapped: An endpoing function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
    """
    request, context = args
    if 'Authorization' not in request.headers:
        context.status_code = codes.UNAUTHORIZED  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.AUTHENTICATION_FAILURE.value,
        }
        return json.dumps(body)

    expected_authorization_header = authorization_header(
        access_key=bytes(instance.access_key, encoding='utf-8'),
        secret_key=bytes(instance.secret_key, encoding='utf-8'),
        method=request.method,
        content=bytes(request.query, encoding='utf-8'),
        content_type=request.headers.get('Content-Type', ''),
        date=request.headers.get('Date', ''),
        request_path=request.path,
    )

    if request.headers['Authorization'] != expected_authorization_header:
        context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_date(wrapped: Callable[..., str],
                  instance: 'MockVuforiaTargetAPI',  # noqa: E501 pylint: disable=unused-argument
                  args: Tuple['MockVuforiaTargetAPI', _RequestObjectProxy,
                              _Context],
                  kwargs: Dict) -> str:
    """
    Validate the date header given to a VWS endpoint.

    Args:
        wrapped: An endpoing function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
    """
    request, context = args

    try:
        date_from_header = datetime.strptime(
            request.headers['Date'],
            '%a, %d %b %Y %H:%M:%S GMT',
        )
    except (KeyError, ValueError):
        context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    time_difference = datetime.now() - date_from_header
    maximum_time_difference = timedelta(minutes=5)

    if abs(time_difference) >= maximum_time_difference:
        context.status_code = codes.FORBIDDEN  # noqa: E501 pylint: disable=no-member

        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.REQUEST_TIME_TOO_SKEWED.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


class Route:
    def __init__(self, route_name, path_pattern, methods):
        self.route_name = route_name
        self.path_pattern = path_pattern
        self.methods = methods


ROUTES = set([])


def route(path_pattern: str, methods: List[str]) -> Callable[..., Callable]:
    """
    Set properties on a decorated method so that it can be recognized as a
    route.

    Args:
        path_pattern: The end part of a URL pattern. E.g. `/targets` or
        `/targets/.+`.
        methods: HTTP methods that map to the route function.
    """
    def decorator(method: Callable[..., str]) -> Callable[
            ..., str]:
        """
        Set properties on a decorated method so that it can be recognized as a
        route.

        Args:
            method: Method to add attributes to.

        Returns:
            Method with attributes added to it.
        """
        route = Route(
            route_name=method.__name__,
            path_pattern=path_pattern,
            methods=methods,
        )
        ROUTES.add(route)
        return method
    return decorator


class MockVuforiaTargetAPI:  # pylint: disable=no-self-use
    """
    A fake implementation of the Vuforia Target API.

    This implementation is tied to the implementation of `requests_mock`.
    """

    def __init__(self, access_key: str, secret_key: str) -> None:
        """
        Args:
            access_key: A VWS access key.
            secret_key: A VWS secret key.

        Attributes:
            access_key: A VWS access key.
            secret_key: A VWS secret key.
        """
        self.access_key = access_key  # type: str
        self.secret_key = secret_key  # type: str

        self.routes = []
        for route in ROUTES:
            route.endpoint = getattr(self, route.route_name)
            self.routes.append(route)

    @validate_authorization
    @validate_date
    @route(path_pattern='/summary', methods=[GET])
    def database_summary(self,
                         request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                         context: _Context) -> str:
        """
        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Get-a-Database-Summary-Report-Using-the-VWS-API
        """
        body = {}  # type: Dict[str, str]

        context.status_code = codes.OK  # pylint: disable=no-member
        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'transaction_id': uuid.uuid4().hex,
            'name': '',
            'active_images': '',
            'inactive_images': '',
            'failed_images': '',
            'target_quota': '',
            'total_recos': '',
            'current_month_recos': '',
            'previous_month_recos': '',
            'processing_images': '',
            'reco_threshold': '',
            'request_quota': '',
            'request_usage': '',
        }
        return json.dumps(body)

    @validate_authorization
    @validate_date
    @route(path_pattern='/targets', methods=[GET])
    def target_list(self,
                    request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                    context: _Context) -> str:
        """
        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Get-a-Target-List-for-a-Cloud-Database-Using-the-VWS-API
        """
        body = {}  # type: Dict[str, Union[str, List[object]]]

        context.status_code = codes.OK  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.SUCCESS.value,
            'results': [],
        }
        return json.dumps(body)
