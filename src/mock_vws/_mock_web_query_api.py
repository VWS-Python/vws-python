"""
A fake implementation of the Vuforia Web Query API.

See
https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
"""

import cgi
import datetime
import io
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Set, Tuple, Union

import pytz
import wrapt
from PIL import Image
from requests import codes
from requests_mock import POST
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from mock_vws._constants import ResultCodes, TargetStatuses
from mock_vws._mock_common import Route, json_dump, set_content_length_header
from mock_vws._mock_web_services_api import MockVuforiaWebServicesAPI, Target

from ._validators import validate_auth_header_exists, validate_authorization

ROUTES = set([])


@wrapt.decorator
def validate_image_format(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the format of the image given to the query endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNPROCESSABLE_ENTITY` response if the image is given and is not
        either a PNG or a JPEG.
    """
    request, context = args
    body_file = io.BytesIO(request.body)

    _, pdict = cgi.parse_header(request.headers['Content-Type'])
    parsed = cgi.parse_multipart(
        fp=body_file,
        pdict={
            'boundary': pdict['boundary'].encode(),
        },
    )

    [image] = parsed['image']

    image_file = io.BytesIO(image)
    pil_image = Image.open(image_file)

    if pil_image.format in ('PNG', 'JPEG'):
        return wrapped(*args, **kwargs)

    context.status_code = codes.UNPROCESSABLE_ENTITY
    transaction_id = uuid.uuid4().hex
    result_code = ResultCodes.BAD_IMAGE.value

    # The response has an unusual format of separators, so we construct it
    # manually.
    return (
        '{"transaction_id": '
        f'"{transaction_id}",'
        f'"result_code":"{result_code}"'
        '}'
    )


@wrapt.decorator
def validate_image_file_contents(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the format of the image given to the query endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNPROCESSABLE_ENTITY` response if the image is given and is not
        either a PNG or a JPEG.
    """
    request, context = args
    body_file = io.BytesIO(request.body)

    _, pdict = cgi.parse_header(request.headers['Content-Type'])
    parsed = cgi.parse_multipart(
        fp=body_file,
        pdict={
            'boundary': pdict['boundary'].encode(),
        },
    )

    [image] = parsed['image']

    image_file = io.BytesIO(image)
    try:
        Image.open(image_file).verify()
    except SyntaxError:
        context.status_code = codes.UNPROCESSABLE_ENTITY
        transaction_id = uuid.uuid4().hex
        result_code = ResultCodes.BAD_IMAGE.value

        # The response has an unusual format of separators, so we construct it
        # manually.
        return (
            '{"transaction_id": '
            f'"{transaction_id}",'
            f'"result_code":"{result_code}"'
            '}'
        )

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_date_header_given(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the date header is given to the query endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response if the date is not given.
    """
    request, context = args

    if 'Date' in request.headers:
        return wrapped(*args, **kwargs)

    context.status_code = codes.BAD_REQUEST
    content_type = 'text/plain; charset=ISO-8859-1'
    context.headers['Content-Type'] = content_type
    return 'Date header required.'


@wrapt.decorator
def validate_max_num_results(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the ``max_num_results`` field is either an integer within range or
    not given.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response if the ``max_num_results`` field is either not
        an integer, or an integer out of range.
    """
    request, context = args
    body_file = io.BytesIO(request.body)

    _, pdict = cgi.parse_header(request.headers['Content-Type'])
    parsed = cgi.parse_multipart(
        fp=body_file,
        pdict={
            'boundary': pdict['boundary'].encode(),
        },
    )
    [max_num_results] = parsed.get('max_num_results', [b'1'])
    invalid_type_error = (
        f"Invalid value '{max_num_results.decode()}' in form data part "
        "'max_result'. "
        'Expecting integer value in range from 1 to 50 (inclusive).'
    )

    try:
        max_num_results_int = int(max_num_results)
    except ValueError:
        context.status_code = codes.BAD_REQUEST
        return invalid_type_error

    java_max_int = 2147483647
    if max_num_results_int > java_max_int:
        context.status_code = codes.BAD_REQUEST
        return invalid_type_error

    if max_num_results_int < 1 or max_num_results_int > 50:
        context.status_code = codes.BAD_REQUEST
        out_of_range_error = (
            f'Integer out of range ({max_num_results_int}) in form data part '
            "'max_result'. Accepted range is from 1 to 50 (inclusive)."
        )
        return out_of_range_error

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_include_target_data(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the ``include_target_data`` field is either an accepted value or
    not given.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response if the ``include_target_data`` field is not an
        accepted value.
    """
    request, context = args
    body_file = io.BytesIO(request.body)

    _, pdict = cgi.parse_header(request.headers['Content-Type'])
    parsed = cgi.parse_multipart(
        fp=body_file,
        pdict={
            'boundary': pdict['boundary'].encode(),
        },
    )

    [include_target_data] = parsed.get('include_target_data', [b'top'])
    include_target_data = include_target_data.lower()
    allowed_included_target_data = {b'top', b'all', b'none'}
    if include_target_data in allowed_included_target_data:
        return wrapped(*args, **kwargs)

    unexpected_target_data_message = (
        f"Invalid value '{include_target_data.decode()}' in form data part "
        "'include_target_data'. "
        "Expecting one of the (unquoted) string values 'all', 'none' or 'top'."
    )
    context.status_code = codes.BAD_REQUEST
    return unexpected_target_data_message


@wrapt.decorator
def validate_date_format(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the format of the date header given to the query endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNAUTHORIZED` response if the date is in the wrong format.
    """
    request, context = args

    try:
        date_from_header = datetime.datetime.strptime(
            request.headers['Date'],
            '%a, %d %b %Y %H:%M:%S GMT',
        )
    except ValueError:
        context.status_code = codes.UNAUTHORIZED
        context.headers['WWW-Authenticate'] = 'VWS'
        text = 'Malformed date header.'
        content_type = 'text/plain; charset=ISO-8859-1'
        context.headers['Content-Type'] = content_type
        return text

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_date(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate date in the date header given to the query endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `FORBIDDEN` response if the date is out of range.
    """
    request, context = args

    date_from_header = datetime.datetime.strptime(
        request.headers['Date'],
        '%a, %d %b %Y %H:%M:%S GMT',
    )

    gmt = pytz.timezone('GMT')
    now = datetime.datetime.now(tz=gmt)
    date_from_header = date_from_header.replace(tzinfo=gmt)
    time_difference = now - date_from_header

    maximum_time_difference = datetime.timedelta(minutes=65)

    if abs(time_difference) < maximum_time_difference:
        return wrapped(*args, **kwargs)

    context.status_code = codes.FORBIDDEN

    body = {
        'transaction_id': uuid.uuid4().hex,
        'result_code': ResultCodes.REQUEST_TIME_TOO_SKEWED.value,
    }
    return json_dump(body)


@wrapt.decorator
def validate_content_type_header(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the ``Content-Type`` header.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An ``UNSUPPORTED_MEDIA_TYPE`` response if the ``Content-Type`` header
        main part is not 'multipart/form-data'.
        A ``BAD_REQUEST`` response if the ``Content-Type`` header does not
        contain a boundary which is in the request body.
    """
    request, context = args

    main_value, pdict = cgi.parse_header(request.headers['Content-Type'])
    if main_value != 'multipart/form-data':
        context.status_code = codes.UNSUPPORTED_MEDIA_TYPE
        context.headers.pop('Content-Type')
        return ''

    if 'boundary' not in pdict:
        context.status_code = codes.BAD_REQUEST
        context.headers['Content-Type'] = 'text/html'
        return (
            'java.io.IOException: RESTEASY007550: '
            'Unable to get boundary for multipart'
        )

    if pdict['boundary'].encode() not in request.body:
        context.status_code = codes.BAD_REQUEST
        context.headers['Content-Type'] = 'text/html'
        return (
            'java.lang.RuntimeException: RESTEASY007500: '
            'Could find no Content-Disposition header within part'
        )

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_accept_header(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the accept header.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `NOT_ACCEPTABLE` response if the Accept header is given and is not
        'application/json' or '*/*'.
    """
    request, context = args

    accept = request.headers.get('Accept')
    if accept in ('application/json', '*/*', None):
        return wrapped(*args, **kwargs)

    context.headers.pop('Content-Type')
    context.status_code = codes.NOT_ACCEPTABLE
    return ''


@wrapt.decorator
def validate_image_field_given(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that the image field is given.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A ``BAD_REQUEST`` response if the image field is not given.
    """
    request, context = args
    body_file = io.BytesIO(request.body)

    _, pdict = cgi.parse_header(request.headers['Content-Type'])
    parsed = cgi.parse_multipart(
        fp=body_file,
        pdict={
            'boundary': pdict['boundary'].encode(),
        },
    )

    if 'image' in parsed.keys():
        return wrapped(*args, **kwargs)

    context.status_code = codes.BAD_REQUEST
    return 'No image.'


@wrapt.decorator
def validate_extra_fields(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that the no unknown fields are given.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A ``BAD_REQUEST`` response if extra fields are given.
    """
    request, context = args
    body_file = io.BytesIO(request.body)

    _, pdict = cgi.parse_header(request.headers['Content-Type'])
    parsed = cgi.parse_multipart(
        fp=body_file,
        pdict={
            'boundary': pdict['boundary'].encode(),
        },
    )

    known_parameters = {'image', 'max_num_results', 'include_target_data'}

    if not parsed.keys() - known_parameters:
        return wrapped(*args, **kwargs)

    context.status_code = codes.BAD_REQUEST
    return 'Unknown parameters in the request.'


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
            validate_date_format,
            validate_date_header_given,
            validate_include_target_data,
            validate_max_num_results,
            validate_image_file_contents,
            validate_image_format,
            validate_image_field_given,
            validate_extra_fields,
            validate_content_type_header,
            validate_accept_header,
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
        mock_web_services_api: MockVuforiaWebServicesAPI,
        query_recognizes_deletion_seconds: Union[int, float],
    ) -> None:
        """
        Args:
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.
            mock_web_services_api: An instance of a mock web services API.
            query_recognizes_deletion_seconds: The number of seconds after a
                target has been deleted that the query endpoint will return a
                500 response for on a match.

        Attributes:
            routes: The `Route`s to be used in the mock.
            access_key (str): A VWS client access key.
            secret_key (str): A VWS client secret key.
            mock_web_services_api (MockVuforiaWebServicesAPI): An instance of a
                mock web services API.
            query_recognizes_deletion_seconds (int): The number of seconds
                after a target has been deleted that the query endpoint will
                return a 500 response for on a match.
        """
        self.routes: Set[Route] = ROUTES
        self.access_key: str = client_access_key
        self.secret_key: str = client_secret_key
        self.mock_web_services_api = mock_web_services_api
        self.query_recognizes_deletion_seconds = (
            query_recognizes_deletion_seconds
        )

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

        [include_target_data] = parsed.get('include_target_data', [b'top'])
        include_target_data = include_target_data.lower()

        [image] = parsed['image']
        matches: Set[Target] = set([])
        gmt = pytz.timezone('GMT')
        now = datetime.datetime.now(tz=gmt)

        minimum_time_since_delete = datetime.timedelta(
            seconds=self.query_recognizes_deletion_seconds,
        )

        for target in self.mock_web_services_api.targets:
            delete_processing = bool(
                target.delete_date
                and (now - target.delete_date) < minimum_time_since_delete,
            )
            if target.image.getvalue() == image:
                if target.status == TargetStatuses.PROCESSING.value:
                    # We return an example 500 response.
                    # Each response given by Vuforia is different.
                    #
                    # Sometimes Vuforia will do the equivalent of `continue`
                    # here, but we choose to:
                    # * Do the most unexpected thing.
                    # * Be consistent with every response.
                    resources_dir = Path(__file__).parent / 'resources'
                    filename = 'match_processing_response'
                    match_processing_resp_file = resources_dir / filename
                    context.status_code = codes.INTERNAL_SERVER_ERROR
                    cache_control = 'must-revalidate,no-cache,no-store'
                    context.headers['Cache-Control'] = cache_control
                    content_type = 'text/html; charset=ISO-8859-1'
                    context.headers['Content-Type'] = content_type
                    return Path(match_processing_resp_file).read_text()
                if target.active_flag and delete_processing:
                    # We return an example 500 response.
                    # Each response given by Vuforia is different.
                    resources_dir = Path(__file__).parent / 'resources'
                    filename = 'match_processing_response'
                    match_processing_resp_file = resources_dir / filename
                    context.status_code = codes.INTERNAL_SERVER_ERROR
                    cache_control = 'must-revalidate,no-cache,no-store'
                    context.headers['Cache-Control'] = cache_control
                    content_type = 'text/html; charset=ISO-8859-1'
                    context.headers['Content-Type'] = content_type
                    return Path(match_processing_resp_file).read_text()
                if (
                    target.active_flag and not target.delete_date
                    and target.status == TargetStatuses.SUCCESS.value
                ):
                    matches.add(target)

        results: List[Dict[str, Any]] = []
        for target in matches:
            target_timestamp = target.last_modified_date.timestamp()
            target_data = {
                'target_timestamp': int(target_timestamp),
                'name': target.name,
                'application_metadata': target.application_metadata,
            }

            if include_target_data == b'all':
                result = {
                    'target_id': target.target_id,
                    'target_data': target_data,
                }
            elif include_target_data == b'top' and not results:
                result = {
                    'target_id': target.target_id,
                    'target_data': target_data,
                }
            else:
                result = {
                    'target_id': target.target_id,
                }

            results.append(result)

        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'results': results[:int(max_num_results)],
            'query_id': uuid.uuid4().hex,
        }

        value = json_dump(body)
        return value
