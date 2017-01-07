"""
A fake implementation of VWS.
"""

import json
import numbers
import uuid
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import (  # noqa F401
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import wrapt
from requests import codes
from requests_mock import DELETE, GET, POST, PUT
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from common.constants import ResultCodes
from vws._request_utils import authorization_header


@wrapt.decorator
def validate_not_invalid_json(wrapped: Callable[..., str],
                              instance: 'MockVuforiaTargetAPI',  # noqa: E501 pylint: disable=unused-argument
                              args: Tuple[_RequestObjectProxy, _Context],
                              kwargs: Dict) -> str:
    """
    Validate that there is either no JSON given or the JSON given is valid.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNAUTHORIZED` response if there is invalid JSON given to the
        database summary endpoint.
        A `BAD_REQUEST` response with a FAIL result code if there is invalid
        JSON given to a POST request.
        A `BAD_REQUEST` with empty text if there is invalid JSON given to
        another request type.
    """
    request, context = args

    if request.text is None:
        return wrapped(*args, **kwargs)

    try:
        json.loads(request.text)
    except JSONDecodeError:
        if request.path == '/summary':
            context.status_code = codes.UNAUTHORIZED  # noqa: E501 pylint: disable=no-member
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.AUTHENTICATION_FAILURE.value,
            }
            return json.dumps(body)
        elif request.method in (POST, PUT):
            context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.FAIL.value,
            }
            return json.dumps(body)

        context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
        context.headers.pop('Content-Type')
        return ''

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_auth_header_exists(
        wrapped: Callable[..., str],
        instance: 'MockVuforiaTargetAPI',  # noqa: E501 pylint: disable=unused-argument
        args: Tuple[_RequestObjectProxy, _Context],
        kwargs: Dict) -> str:
    """
    Validate that there is an authorization header given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNAUTHORIZED` response if there is no "Authorization" header.
    """
    request, context = args
    if 'Authorization' not in request.headers:
        context.status_code = codes.UNAUTHORIZED  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.AUTHENTICATION_FAILURE.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_authorization(wrapped: Callable[..., str],
                           instance: 'MockVuforiaTargetAPI',
                           args: Tuple[_RequestObjectProxy, _Context],
                           kwargs: Dict) -> str:
    """
    Validate the authorization header given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response if the "Authorization" header is not as
        expected.
    """
    request, context = args

    if request.text is None:
        content = b''
    else:
        content = bytes(request.text, encoding='utf-8')

    expected_authorization_header = authorization_header(
        access_key=bytes(instance.access_key, encoding='utf-8'),
        secret_key=bytes(instance.secret_key, encoding='utf-8'),
        method=request.method,
        content=content,
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
                  args: Tuple[_RequestObjectProxy, _Context],
                  kwargs: Dict) -> str:
    """
    Validate the date header given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
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


def validate_keys(mandatory_keys: Set[str],
                  optional_keys: Set[str]) -> Callable:
    """
    Args:
        mandatory_keys: TODO
        optional_keys: TODO
    """
    @wrapt.decorator
    def wrapper(wrapped: Callable[..., str],
                instance: 'MockVuforiaTargetAPI',  # noqa: E501 pylint: disable=unused-argument
                args: Tuple[_RequestObjectProxy, _Context],
                kwargs: Dict,
               ) -> str:
        """
        Validate the request keys given to a VWS endpoint.

        Args:
            wrapped: An endpoint function for `requests_mock`.
            instance: The class that the endpoint function is in.
            args: The arguments given to the endpoint function.
            kwargs: The keyword arguments given to the endpoint function.

        Returns:
            The result of calling the endpoint.
        """
        request, context = args
        allowed_keys = mandatory_keys.union(optional_keys)

        if request.text is None and not allowed_keys:
            return wrapped(*args, **kwargs)

        request_body_json = json.loads(request.text)
        given_keys = set(request_body_json.keys())
        all_given_keys_allowed = given_keys.issubset(allowed_keys)
        all_mandatory_keys_given = mandatory_keys.issubset(given_keys)

        if all_given_keys_allowed and all_mandatory_keys_given:
            return wrapped(*args, **kwargs)

        context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapper


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


def route(
        path_pattern: str,
        methods: List[str],
        mandatory_keys: Optional[Set[str]]=None,
        optional_keys: Optional[Set[str]]=None) -> Callable[..., Callable]:
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

        key_validator = validate_keys(
            optional_keys=optional_keys or set([]),
            mandatory_keys=mandatory_keys or set([]),
        )

        # There is an undocumented difference in behavior between `/summary`
        # and other endpoints.
        if path_pattern == '/summary':
            validators = [
                validate_authorization,
                key_validator,
                validate_not_invalid_json,
                validate_date,
                validate_auth_header_exists,
            ]
        else:
            validators = [
                validate_authorization,
                key_validator,
                validate_date,
                validate_not_invalid_json,
                validate_auth_header_exists,
            ]

        for validator in validators:
            method = validator(method)

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
            routes: The `Route`s to be used in the mock.
        """
        self.access_key = access_key  # type: str
        self.secret_key = secret_key  # type: str

        self.routes = ROUTES  # type: Set[Route]

    @route(
        path_pattern='/targets',
        methods=[POST],
        mandatory_keys={'image', 'width', 'name'},
        optional_keys={'active_flag', 'application_metadata'},
    )
    def add_target(self,
                   request: _RequestObjectProxy,
                   context: _Context) -> str:
        """
        Add a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-to-Add-a-Target-Using-VWS-API
        """
        width = request.json().get('width')
        name = request.json().get('name')

        width_is_number = isinstance(width, numbers.Number)
        width_positive = width_is_number and width >= 0

        name_is_string = isinstance(name, str)
        name_valid_length = name_is_string and 0 < len(name) < 65

        if not all([width_positive, name_valid_length]):
            context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.FAIL.value,
            }
            return json.dumps(body)

        context.status_code = codes.CREATED  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.TARGET_CREATED.value,
            'target_id': uuid.uuid4().hex,
        }
        return json.dumps(body)

    @route(path_pattern='/targets/.+', methods=[DELETE])
    def delete_target(self,
                      request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                      context: _Context) -> str:
        """
        Delete a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Delete-a-Target-Using-the-VWS-API
        """
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.UNKNOWN_TARGET.value,
        }  # type: Dict[str, str]
        context.status_code = codes.NOT_FOUND  # noqa: E501 pylint: disable=no-member

        return json.dumps(body)

    @route(path_pattern='/summary', methods=[GET])
    def database_summary(self,
                         request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                         context: _Context) -> str:
        """
        Get a database summary report.

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

    @route(path_pattern='/targets', methods=[GET])
    def target_list(self,
                    request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                    context: _Context) -> str:
        """
        Get a list of all targets.

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
                   context: _Context) -> str:
        """
        Get details of a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Record-Using-the-VWS-API
        """
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.UNKNOWN_TARGET.value,
        }  # type: Dict[str, str]
        context.status_code = codes.NOT_FOUND  # noqa: E501 pylint: disable=no-member

        return json.dumps(body)

    @route(path_pattern='/duplicates/.+', methods=[GET])
    def get_duplicates(self,
                       request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                       context: _Context) -> str:
        """
        Get targets which may be considered duplicates of a given target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Check-for-Duplicate-Targets-using-the-VWS-API
        """
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.UNKNOWN_TARGET.value,
        }  # type: Dict[str, str]
        context.status_code = codes.NOT_FOUND  # noqa: E501 pylint: disable=no-member

        return json.dumps(body)

    @route(path_pattern='/targets/.+', methods=[PUT])
    def update_target(self,
                      request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                      context: _Context) -> str:
        """
        Update a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Update-a-Target-Using-the-VWS-API
        """
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.UNKNOWN_TARGET.value,
        }  # type: Dict[str, str]
        context.status_code = codes.NOT_FOUND  # noqa: E501 pylint: disable=no-member

        return json.dumps(body)

    @route(path_pattern='/summary/.+', methods=[GET])
    def target_summary(self,
                       request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                       context: _Context) -> str:
        """
        Get a summary report for a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Summary-Report-using-the-VWS-API
        """
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.UNKNOWN_TARGET.value,
        }  # type: Dict[str, str]
        context.status_code = codes.NOT_FOUND  # noqa: E501 pylint: disable=no-member

        return json.dumps(body)
