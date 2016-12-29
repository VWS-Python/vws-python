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
                           args: Union[
                               Tuple[_RequestObjectProxy, _Context],
                               Tuple[_RequestObjectProxy, _Context, str]],
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
    request = args[0]
    context = args[1]

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
# TODO Validate headers of all routes
def validate_date(wrapped: Callable[..., str],
                  instance: 'MockVuforiaTargetAPI',  # noqa: E501 pylint: disable=unused-argument
                  args: Union[
                      Tuple[_RequestObjectProxy, _Context],
                      Tuple[_RequestObjectProxy, _Context, str]],
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
    request = args[0]
    context = args[1]

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
    """
    A container for the route details which `requests_mock` needs.

    We register routes with names, and when we have an instance to work with
    later.
    """

    def __init__(self, route_name: str, path_pattern: str,
                 methods: List[str]) -> None:
        """
        Args:
            route_name: The name of the method.
            path_pattern: The end part of a URL pattern. E.g. `/targets` or
                `/targets/.+`.
            methods: HTTP methods that map to the route function.

        Attributes:
            route_name: The name of the method.
            path_pattern: The end part of a URL pattern. E.g. `/targets` or
                `/targets/.+`.
            methods: HTTP methods that map to the route function.
            endpoint: The method `requests_mock` should call when the endpoint
                is requested.
        """
        self.route_name = route_name
        self.path_pattern = path_pattern
        self.methods = methods


ROUTES = set([])


@wrapt.decorator
def parse_path(wrapped: Callable[..., str],
               instance: 'MockVuforiaTargetAPI',
               args: Union[
                   Tuple[_RequestObjectProxy, _Context],
                   Tuple[_RequestObjectProxy, _Context, str]],
               kwargs: Dict) -> str:
    """Give the decorated function a "target_id" parameter if given.

    If a path has multiple parts (e.g. `/summary/thing`) then the only thing
    which the VWS API accepts as a final part is a target's id.

    Therefore, if there is an extra part on the end of the path, validate this
    path, and give it to the route method as a parameter.

    Args:
        wrapped: An endpoing function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
    """
    def _execute(request: _RequestObjectProxy,
                 context: _Context,
                 *_args: Tuple,
                 **_kwargs: Dict) -> str:
        """
        See `path_pattern`.
        """

        try:
            _, _, target_id = request.path.split('/')
        except ValueError:
            return wrapped(request, context, *_args, **_kwargs)

        cloud_target_ids = set(
            [target.target_id for target in instance.targets])

        if target_id not in cloud_target_ids:
            context.status_code = codes.NOT_FOUND  # pylint: disable=no-member

            body = {}  # type: Dict[str, str]
            return json.dumps(body)
        return wrapped(request, context, target_id, *_args, **_kwargs)

    return _execute(*args, **kwargs)


def route(path_pattern: str, methods: List[str]) -> Callable[..., Callable]:
    """
    Register a decorated method so that it can be recognized as a route.

    Args:
        path_pattern: The end part of a URL pattern. E.g. `/targets` or
            `/targets/.+`.
        methods: HTTP methods that map to the route function.
    """
    def decorator(method: Callable[..., str]) -> Callable[
            ..., str]:
        """
        Register a decorated method so that it can be recognized as a route.

        Args:
            method: Method to register.

        Returns:
            The given `method` with no changes.
        """
        ROUTES.add(
            Route(
                route_name=method.__name__,
                path_pattern=path_pattern,
                methods=methods,
            )
        )
        # pylint is not very good with decorators
        # https://github.com/PyCQA/pylint/issues/259#issuecomment-267671718
        return parse_path(method)  # pylint: disable=no-value-for-parameter
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
            routes: The `Route`s to be used in the mock.
        """
        self.access_key = access_key  # type: str
        self.secret_key = secret_key  # type: str

        self.routes = ROUTES  # type: Set[Route]
        self.targets = []  # type: List

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

    @route(path_pattern='/targets/.+', methods=[GET])
    def get_target(self,
                   request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                   context: _Context,
                   target_id: str) -> str:
        """
        XXX
        """
