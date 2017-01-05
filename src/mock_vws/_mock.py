"""
A fake implementation of VWS.
"""

import base64
import imghdr
import io
import json
import numbers
import uuid
from datetime import datetime, timedelta
from functools import partial
from json.decoder import JSONDecodeError
from typing import (  # noqa F401
    Any,
    Callable,
    Dict,
    List,
    Tuple,
    Union,
    Optional,
)

import wrapt
from requests import codes
from requests_mock import DELETE, GET, POST, PUT
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from common.constants import ResultCodes
from vws._request_utils import authorization_header


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
    """
    request, context = args
    if 'Authorization' not in request.headers:
        context.status_code = codes.UNAUTHORIZED  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.AUTHENTICATION_FAILURE.value,
        }
        return json.dumps(body)

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


def validate_keys(mandatory_keys, optional_keys):
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

        try:
            decoded_body = request.body.decode('ascii')
        except AttributeError:
            decoded_body = ''

        try:
            request_body_json = json.loads(decoded_body)
        except JSONDecodeError:
            if request.path == '/summary':
                context.status_code = codes.UNAUTHORIZED  # noqa: E501 pylint: disable=no-member
                body = {
                    'transaction_id': uuid.uuid4().hex,
                    'result_code': ResultCodes.AUTHENTICATION_FAILURE.value,
                }
                return json.dumps(body)
            request_body_json = {}
            if not allowed_keys:
                # TODO do content type
                context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
                return ''

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
    mandatory_keys: Optional[List[str]]=None,
    optional_keys: Optional[List[str]]=None,
) -> Callable[..., Callable]:
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
        date_validated = validate_date(method)  # noqa: E501 pylint: disable=no-value-for-parameter
        authorization_validated = validate_authorization(date_validated)  # noqa: E501 pylint: disable=no-value-for-parameter
        key_validator = validate_keys(
            optional_keys=optional_keys or set([]),
            mandatory_keys=mandatory_keys or set([]),
        )
        keys_validated = key_validator(authorization_validated)
        return keys_validated
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
                   request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
                   context: _Context,
                   ) -> str:
        """
        Add a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-to-Add-a-Target-Using-VWS-API
        """
        body = {}  # type: Dict[str, Union[str, int]]
        decoded_body = request.body.decode('ascii')
        request_body_json = json.loads(decoded_body)

        valid = True
        width = request_body_json.get('width')
        name = request_body_json.get('name')

        width_is_number = isinstance(width, numbers.Number)
        width_positive = width_is_number and width >= 0
        valid = valid and width_positive

        valid = valid and isinstance(name, str)
        valid = valid and 0 < len(name) < 65

        if not valid:
            context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.FAIL.value,
            }
            return json.dumps(body)

        image = request_body_json.get('image')
        decoded = base64.b64decode(image)
        image_file = io.BytesIO(decoded)
        image_file_type = imghdr.what(image_file)

        if image_file_type not in ('png', 'jpeg'):
            context.status_code = codes.UNPROCESSABLE_ENTITY  # noqa: E501 pylint: disable=no-member
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.BAD_IMAGE.value,
            }
            return json.dumps(body)

        context.status_code = codes.CREATED  # noqa: E501 pylint: disable=no-member
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
