"""
A fake implementation of VWS.
"""

import base64
import datetime
import email.utils
import io
import json
import random
import statistics
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
from PIL import Image, ImageStat
from requests import codes
from requests_mock import DELETE, GET, POST, PUT
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from mock_vws._constants import ResultCodes, TargetStatuses

from ._constants import States
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
    kwargs: Dict,
) -> str:
    """
    Parse a target ID in a URL path and give the method a target argument.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        If a target ID is given in the path then the wrapped function is given
        an extra argument - the matching target.
        A `NOT_FOUND` response if there is no matching target.
    """
    request, context = args

    split_path = request.path.split('/')

    if len(split_path) == 2:
        return wrapped(*args, **kwargs)

    target_id = split_path[-1]

    try:
        [matching_target] = [
            target for target in instance.targets
            if target.target_id == target_id
        ]
    except ValueError:
        body: Dict[str, str] = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.UNKNOWN_TARGET.value,
        }
        context.status_code = codes.NOT_FOUND
        return json.dumps(body)

    new_args = args + (matching_target, )
    return wrapped(*new_args, **kwargs)


@wrapt.decorator
def headers(
    wrapped: Callable[..., str],
    instance: 'MockVuforiaTargetAPI',  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict
) -> str:
    """
    Set the `Content-Length` and `Date` headers.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
    """
    _, context = args

    result = wrapped(*args, **kwargs)
    context.headers['Content-Length'] = str(len(result))
    date = email.utils.formatdate(None, localtime=False, usegmt=True)
    context.headers['Date'] = date
    return result


class Route:
    """
    A container for the route details which `requests_mock` needs.

    We register routes with names, and when we have an instance to work with
    later.
    """

    def __init__(
        self,
        route_name: str,
        path_pattern: str,
        http_methods: List[str],
    ) -> None:
        """
        Args:
            route_name: The name of the method.
            path_pattern: The end part of a URL pattern. E.g. `/targets` or
                `/targets/.+`.
            http_methods: HTTP methods that map to the route function.

        Attributes:
            route_name: The name of the method.
            path_pattern: The end part of a URL pattern. E.g. `/targets` or
                `/targets/.+`.
            http_methods: HTTP methods that map to the route function.
            endpoint: The method `requests_mock` should call when the endpoint
                is requested.
        """
        self.route_name = route_name
        self.path_pattern = path_pattern
        self.http_methods = http_methods


ROUTES = set([])


def route(
    path_pattern: str,
    http_methods: List[str],
    mandatory_keys: Optional[Set[str]] = None,
    optional_keys: Optional[Set[str]] = None,
) -> Callable[..., Callable]:
    """
    Register a decorated method so that it can be recognized as a route.

    Args:
        path_pattern: The end part of a URL pattern. E.g. `/targets` or
            `/targets/.+`.
        http_methods: HTTP methods that map to the route function.
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
                http_methods=http_methods,
            )
        )

        key_validator = validate_keys(
            optional_keys=optional_keys or set([]),
            mandatory_keys=mandatory_keys or set([]),
        )

        # There is an undocumented difference in behavior between `/summary`
        # and other endpoints.
        if path_pattern == '/summary':
            decorators = [
                validate_authorization,
                key_validator,
                validate_not_invalid_json,
                validate_date,
                validate_auth_header_exists,
                headers,
            ]
        else:
            decorators = [
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
                headers,
            ]

        for decorator in decorators:
            method = decorator(method)

        return method

    return decorator


class Target:  # pylint: disable=too-many-instance-attributes
    """
    A Vuforia Target as managed in
    https://developer.vuforia.com/target-manager.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        active_flag: bool,
        width: float,
        image: io.BytesIO,
        processing_time_seconds: Union[int, float],
    ) -> None:
        """
        Args:
            name: The name of the target.
            active_flag: Whether or not the target is active for query.
            width: The width of the image in scene unit.
            image: The image associated with the target.
            processing_time_seconds: The number of seconds to process each
                image for. In the real Vuforia Web Services, this is not
                deterministic.

        Attributes:
            name (str): The name of the target.
            target_id (str): The unique ID of the target.
            active_flag (bool): Whether or not the target is active for query.
            width (int): The width of the image in scene unit.
            upload_date (datetime.datetime): The time that the target was
                created.
            last_modified_date (datetime.datetime): The time that the target
                was last modified.
            processed_tracking_rating (int): The tracking rating of the target
                once it has been processed.
            image (io.BytesIO): The image data associated with the target.
            reco_rating (str): An empty string ("for now" according to
                Vuforia's documentation).
        """
        self.name = name
        self.target_id = uuid.uuid4().hex
        self.active_flag = active_flag
        self.width = width
        self.upload_date: datetime.datetime = datetime.datetime.now()
        self.last_modified_date = self.upload_date
        self.processed_tracking_rating = random.randint(0, 5)
        self.image = image
        self.reco_rating = ''
        self._processing_time_seconds = processing_time_seconds

    @property
    def _post_processing_status(self) -> TargetStatuses:
        """
        Return the status of the target, or what it will be when processing is
        finished.

        The status depends on the standard deviation of the color bands.
        How VWS determines this is unknown, but it relates to how suitable the
        target is for detection.
        """
        image = Image.open(self.image)
        image_stat = ImageStat.Stat(image)

        average_std_dev = statistics.mean(image_stat.stddev)

        if average_std_dev > 5:
            return TargetStatuses.SUCCESS

        return TargetStatuses.FAILED

    @property
    def status(self) -> str:
        """
        Return the status of the target.

        For now this waits half a second (arbitrary) before changing the
        status from 'processing' to 'failed' or 'success'.

        The status depends on the standard deviation of the color bands.
        How VWS determines this is unknown, but it relates to how suitable the
        target is for detection.
        """
        processing_time = datetime.timedelta(
            seconds=self._processing_time_seconds
        )

        time_since_change = datetime.datetime.now() - self.last_modified_date

        if time_since_change <= processing_time:
            return str(TargetStatuses.PROCESSING.value)

        return str(self._post_processing_status.value)

    @property
    def tracking_rating(self) -> int:
        """
        Return the tracking rating of the target recognition image.

        In this implementation that is just a random integer between 0 and 5
        if the target status is 'success'.
        The rating is 0 if the target status is 'failed'.
        The rating is -1 for a short time while the target is being processed.
        The real VWS seems to give -1 for a short time while processing, then
        the real rating, even while it is still processing.
        """
        pre_rating_time = datetime.timedelta(
            # That this is half of the total processing time is unrealistic.
            # In VWS it is not a constant percentage.
            seconds=self._processing_time_seconds / 2
        )

        time_since_upload = datetime.datetime.now() - self.upload_date

        if time_since_upload <= pre_rating_time:
            return -1

        if self._post_processing_status == TargetStatuses.SUCCESS:
            return self.processed_tracking_rating

        return 0


class MockVuforiaTargetAPI:  # pylint: disable=no-self-use
    """
    A fake implementation of the Vuforia Target API.

    This implementation is tied to the implementation of `requests_mock`.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        server_access_key: str,
        server_secret_key: str,
        database_name: str,
        state: States,
        processing_time_seconds: Union[int, float],
    ) -> None:
        """
        Args:
            database_name: The name of a VWS target manager database.
            server_access_key: A VWS server access key.
            server_secret_key: A VWS server secret key.
            state: The state of the services being mocked.
            processing_time_seconds: The number of seconds to process each
                image for. In the real Vuforia Web Services, this is not
                deterministic.

        Attributes:
            database_name: The name of a VWS target manager database name.
            server_access_key (str): A VWS server access key.
            server_secret_key (str): A VWS server secret key.
            targets: The ``Target``s in the database.
            routes: The `Route`s to be used in the mock.
            state: The state of the services being mocked.
        """
        self.database_name = database_name

        self.server_access_key: str = server_access_key
        self.server_secret_key: str = server_secret_key

        self.targets: List[Target] = []
        self.routes: Set[Route] = ROUTES
        self.state = state

        self._processing_time_seconds = processing_time_seconds

    @route(
        path_pattern='/targets',
        http_methods=[POST],
        mandatory_keys={'image', 'width', 'name'},
        optional_keys={'active_flag', 'application_metadata'},
    )
    def add_target(
        self,
        request: _RequestObjectProxy,
        context: _Context,
    ) -> str:
        """
        Add a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Add-a-Target
        """
        name = request.json()['name']

        if any(target.name == name for target in self.targets):
            context.status_code = codes.FORBIDDEN
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.TARGET_NAME_EXIST.value,
            }
            return json.dumps(body)

        active_flag = request.json().get('active_flag')
        if active_flag is None:
            active_flag = True

        image = request.json()['image']
        decoded = base64.b64decode(image)
        image_file = io.BytesIO(decoded)

        new_target = Target(
            name=request.json()['name'],
            width=request.json()['width'],
            image=image_file,
            active_flag=active_flag,
            processing_time_seconds=self._processing_time_seconds,
        )
        self.targets.append(new_target)

        context.status_code = codes.CREATED
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.TARGET_CREATED.value,
            'target_id': new_target.target_id,
        }
        return json.dumps(body)

    @route(path_pattern='/targets/.+', http_methods=[DELETE])
    def delete_target(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,
        target: Target,
    ) -> str:
        """
        Delete a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Delete-a-Target
        """
        body: Dict[str, str] = {}

        if target.status == TargetStatuses.PROCESSING.value:
            context.status_code = codes.FORBIDDEN
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.TARGET_STATUS_PROCESSING.value,
            }
            return json.dumps(body)

        self.targets = [
            item for item in self.targets if item.target_id != target.target_id
        ]

        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.SUCCESS.value,
        }
        return json.dumps(body)

    @route(path_pattern='/summary', http_methods=[GET])
    def database_summary(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
    ) -> str:
        """
        Get a database summary report.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Get-a-Database-Summary-Report
        """
        body: Dict[str, Union[str, int]] = {}

        active_images = len(
            [
                target for target in self.targets
                if target.status == TargetStatuses.SUCCESS.value
                and target.active_flag
            ]
        )

        failed_images = len(
            [
                target for target in self.targets
                if target.status == TargetStatuses.FAILED.value
            ]
        )

        inactive_images = len(
            [
                target for target in self.targets
                if target.status == TargetStatuses.SUCCESS.value
                and not target.active_flag
            ]
        )

        processing_images = len(
            [
                target for target in self.targets
                if target.status == TargetStatuses.PROCESSING.value
            ]
        )

        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'transaction_id': uuid.uuid4().hex,
            'name': self.database_name,
            'active_images': active_images,
            'inactive_images': inactive_images,
            'failed_images': failed_images,
            'target_quota': '',
            'total_recos': '',
            'current_month_recos': '',
            'previous_month_recos': '',
            'processing_images': processing_images,
            'reco_threshold': '',
            'request_quota': '',
            'request_usage': '',
        }
        return json.dumps(body)

    @route(path_pattern='/targets', http_methods=[GET])
    def target_list(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
    ) -> str:
        """
        Get a list of all targets.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Get-a-Target-List-for-a-Cloud-Database
        """
        results = [target.target_id for target in self.targets]

        body: Dict[str, Union[str, List[str]]] = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.SUCCESS.value,
            'results': results,
        }
        return json.dumps(body)

    @route(path_pattern='/targets/.+', http_methods=[GET])
    def get_target(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
        target: Target,
    ) -> str:
        """
        Get details of a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Retrieve-a-Target-Record
        """
        target_record = {
            'target_id': target.target_id,
            'active_flag': target.active_flag,
            'name': target.name,
            'width': target.width,
            'tracking_rating': target.tracking_rating,
            'reco_rating': target.reco_rating,
        }

        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'transaction_id': uuid.uuid4().hex,
            'target_record': target_record,
            'status': target.status,
        }
        return json.dumps(body)

    @route(path_pattern='/duplicates/.+', http_methods=[GET])
    def get_duplicates(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
        target: Target,  # pylint: disable=unused-argument
    ) -> str:
        """
        Get targets which may be considered duplicates of a given target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Check-for-Duplicate-Targets
        """
        other_targets = set(self.targets) - set([target])

        similar_targets: List[str] = [
            other.target_id for other in other_targets
            if Image.open(other.image) == Image.open(target.image) and
            TargetStatuses.FAILED.value not in (target.status, other.status)
            and TargetStatuses.PROCESSING.value not in
            (target.status, other.status) and other.active_flag
        ]

        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.SUCCESS.value,
            'similar_targets': similar_targets,
        }

        return json.dumps(body)

    @route(
        path_pattern='/targets/.+',
        http_methods=[PUT],
        optional_keys={
            'active_flag',
            'application_metadata',
            'image',
            'name',
            'width',
        },
    )
    def update_target(
        self,
        request: _RequestObjectProxy,
        context: _Context,
        target: Target,
    ) -> str:
        """
        Update a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Update-a-Target
        """
        body: Dict[str, str] = {}

        if target.status != TargetStatuses.SUCCESS.value:
            context.status_code = codes.FORBIDDEN
            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.TARGET_STATUS_NOT_SUCCESS.value,
            }
            return json.dumps(body)

        if 'width' in request.json():
            target.width = request.json()['width']

        if 'active_flag' in request.json():
            active_flag = request.json()['active_flag']
            if active_flag is None:
                body = {
                    'transaction_id': uuid.uuid4().hex,
                    'result_code': ResultCodes.FAIL.value,
                }
                context.status_code = codes.BAD_REQUEST
                return json.dumps(body)
            target.active_flag = active_flag

        if 'application_metadata' in request.json():
            if request.json()['application_metadata'] is None:
                body = {
                    'transaction_id': uuid.uuid4().hex,
                    'result_code': ResultCodes.FAIL.value,
                }
                context.status_code = codes.BAD_REQUEST
                return json.dumps(body)

        if 'name' in request.json():
            name = request.json()['name']
            other_targets = set(self.targets) - set([target])
            if any(other.name == name for other in other_targets):
                context.status_code = codes.FORBIDDEN
                body = {
                    'transaction_id': uuid.uuid4().hex,
                    'result_code': ResultCodes.TARGET_NAME_EXIST.value,
                }
                return json.dumps(body)
            target.name = name

        # In the real implementation, the tracking rating can stay the same.
        # However, for demonstration purposes, the tracking rating changes but
        # when the target is updated.
        available_values = list(set(range(6)) - set([target.tracking_rating]))
        target.processed_tracking_rating = random.choice(available_values)

        target.last_modified_date = datetime.datetime.now()

        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'transaction_id': uuid.uuid4().hex,
        }
        return json.dumps(body)

    @route(path_pattern='/summary/.+', http_methods=[GET])
    def target_summary(
        self,
        request: _RequestObjectProxy,  # pylint: disable=unused-argument
        context: _Context,  # pylint: disable=unused-argument
        target: Target,
    ) -> str:
        """
        Get a summary report for a target.

        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Retrieve-a-Target-Summary-Report
        """
        body = {
            'status': target.status,
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.SUCCESS.value,
            'database_name': self.database_name,
            'target_name': target.name,
            'upload_date': target.upload_date.strftime('%Y-%m-%d'),
            'active_flag': target.active_flag,
            'tracking_rating': target.tracking_rating,
            'total_recos': '',
            'current_month_recos': '',
            'previous_month_recos': '',
        }
        return json.dumps(body)
