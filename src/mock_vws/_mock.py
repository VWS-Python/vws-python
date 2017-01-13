"""
A fake implementation of VWS.
"""

import json
import uuid
from typing import (  # noqa: F401
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

from ._validators import (
    validate_active_flag,
    validate_auth_header_exists,
    validate_authorization,
    validate_date,
    validate_image_color_space,
    validate_image_data_type,
    validate_image_encoding,
    validate_image_format,
    validate_image_is_image,
    validate_image_size,
    validate_keys,
    validate_metadata_encoding,
    validate_metadata_type,
    validate_name,
    validate_not_invalid_json,
    validate_width,
)


@wrapt.decorator
def parse_target_id(
    wrapped: Callable[..., str],
    instance: 'MockVuforiaTargetAPI',
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict
) -> str:
    """
    Parse a target ID in a URL path.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        If a target ID is given in the path then the wrapped function is given
        an extra argument - the target ID.
    """
    request, context = args

    split_path = request.path.split('/')

    if len(split_path) == 2:
        return wrapped(*args, **kwargs)

    target_id = split_path[-1]

    if not any(
        [
            target for target in instance.targets
            if target.target_id == target_id
        ]
    ):
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.UNKNOWN_TARGET.value,
        }  # type: Dict[str, str]
        context.status_code = codes.NOT_FOUND  # pylint: disable=no-member
        return json.dumps(body)

    new_args = args + (target_id, )
    return wrapped(*new_args, **kwargs)


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
    optional_keys: Optional[Set[str]]=None
) -> Callable[..., Callable]:
    """
    Register a decorated method so that it can be recognized as a route.

    Args:
        path_pattern: The end part of a URL pattern. E.g. `/targets` or
            `/targets/.+`.
        methods: HTTP methods that map to the route function.
        mandatory_keys: Keys required by the endpoint.
        optional_keys: Keys which are not required by the endpoint but which
            are allowed.
    """

    def decorator(method: Callable[..., str]) -> Callable[..., str]:
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
                parse_target_id,
                validate_authorization,
                validate_metadata_encoding,
                validate_metadata_type,
                validate_active_flag,
                validate_image_size,
                validate_image_color_space,
                validate_image_format,
                validate_image_is_image,
                validate_image_encoding,
                validate_image_data_type,
                validate_name,
                validate_width,
                key_validator,
                validate_date,
                validate_not_invalid_json,
                validate_auth_header_exists,
            ]

        for validator in validators:
            method = validator(method)

        return method

    return decorator


class Target:
    """
    A Vuforia Target as managed in
    https://developer.vuforia.com/target-manager.
    """

    def __init__(self, name: str) -> None:
        """
        Args:
            name: The name of the target.

        Attributes:
            name (str): The name of the target.
            target_id (str): The unique ID of the target.
        """
        self.name = name
        self.target_id = uuid.uuid4().hex


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

        self.targets = []  # type: List[Target]
        self.routes = ROUTES  # type: Set[Route]

    @route(
        path_pattern='/targets',
        methods=[POST],
        mandatory_keys={'image', 'width', 'name'},
        optional_keys={'active_flag', 'application_metadata'},
    )
    def add_target(
        self, request: _RequestObjectProxy, context: _Context
    ) -> str:
        """
        Add a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-to-Add-a-Target-Using-VWS-API
        """
        name = request.json().get('name')

        if any(target.name == name for target in self.targets):
            context.status_code = codes.FORBIDDEN  # noqa: E501 pylint: disable=no-member
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.TARGET_NAME_EXIST.value,
            }
            return json.dumps(body)

        new_target = Target(name=name)
        self.targets.append(new_target)

        context.status_code = codes.CREATED  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.TARGET_CREATED.value,
            'target_id': new_target.target_id,
        }
        return json.dumps(body)

    @route(path_pattern='/targets/.+', methods=[DELETE])
    def delete_target(
        self,
        request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
        context: _Context,
        target_id: str,
    ) -> str:
        """
        Delete a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Delete-a-Target-Using-the-VWS-API
        """
        body = {}  # type: Dict[str, str]

        target_id = request.path.split('/')[-1]
        for target in self.targets:
            if target.target_id == target_id:
                context.status_code = codes.FORBIDDEN  # noqa: E501 pylint: disable=no-member
                body = {
                    'transaction_id': uuid.uuid4().hex,
                    'result_code': ResultCodes.TARGET_STATUS_PROCESSING.value,
                }
        return json.dumps(body)

    @route(path_pattern='/summary', methods=[GET])
    def database_summary(
        self,
        request: _RequestObjectProxy,  # noqa: E501 pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
    ) -> str:
        """
        Get a database summary report.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Get-a-Database-Summary-Report-Using-the-VWS-API
        """
        body = {}  # type: Dict[str, str]

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
    def target_list(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
    ) -> str:
        """
        Get a list of all targets.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Get-a-Target-List-for-a-Cloud-Database-Using-the-VWS-API
        """
        body = {}  # type: Dict[str, Union[str, List[str]]]

        results = [target.target_id for target in self.targets]

        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.SUCCESS.value,
            'results': results,
        }
        return json.dumps(body)

    @route(path_pattern='/targets/.+', methods=[GET])
    def get_target(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
        target_id: str,
    ) -> str:
        """
        Get details of a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Record-Using-the-VWS-API
        """
        target_record = {
            'target_id': target_id,
            'active_flag': '',
            'name': '',
            'width': '',
            'tracking_rating': '',
            'reco_rating': '',
        }
        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'transaction_id': uuid.uuid4().hex,
            'target_record': target_record,
            'status': 'processing',
        }
        return json.dumps(body)

    @route(path_pattern='/duplicates/.+', methods=[GET])
    def get_duplicates(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,
        target_id: str,  # pylint: disable=unused-argument
    ) -> str:
        """
        Get targets which may be considered duplicates of a given target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Check-for-Duplicate-Targets-using-the-VWS-API
        """

    @route(path_pattern='/targets/.+', methods=[PUT])
    def update_target(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,
        target_id: str,  # pylint: disable=unused-argument
    ) -> str:
        """
        Update a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Update-a-Target-Using-the-VWS-API
        """

    @route(path_pattern='/summary/.+', methods=[GET])
    def target_summary(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,
        target_id: str,  # pylint: disable=unused-argument
    ) -> str:
        """
        Get a summary report for a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Summary-Report-using-the-VWS-API
        """
