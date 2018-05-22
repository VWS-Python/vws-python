"""
A fake implementation of the Vuforia Web Query API.

See
https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
"""

import cgi
import io
import uuid
from json.decoder import JSONDecodeError
from typing import Any, Callable, Dict, List, Set, Tuple

import wrapt
from requests import codes
from requests_mock import POST
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from mock_vws._constants import ResultCodes
from mock_vws._mock_common import Route, json_dump, set_content_length_header
from mock_vws._mock_web_services_api import MockVuforiaWebServicesAPI

from ._validators import (
    validate_auth_header_exists,
    validate_authorization,
    validate_date,
)

ROUTES = set([])


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
def validate_response_body_type(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate body type.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNSUPPORTED_MEDIA_TYPE` response if the request body is valid UTF-8
        encoded text.
    """
    request, context = args

    try:
        request.json()
    except JSONDecodeError:
        context.status_code = codes.BAD_REQUEST
        text = (
            'java.lang.RuntimeException: RESTEASY007500: '
            'Could find no Content-Disposition header within part'
        )
        context.headers['Content-Type'] = 'text/html'
        return text
    except UnicodeDecodeError:
        # This logic is fishy.
        # See https://github.com/adamtheturtle/vws-python/issues/548.
        return wrapped(*args, **kwargs)

    text = ''
    context.status_code = codes.UNSUPPORTED_MEDIA_TYPE
    context.headers.pop('Content-Type')
    return text


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
            validate_content_type_header,
            validate_response_body_type,
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
    ) -> None:
        """
        Args:
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.
            mock_web_services_api: An instance of a mock web services API.

        Attributes:
            routes: The `Route`s to be used in the mock.
            access_key (str): A VWS client access key.
            secret_key (str): A VWS client secret key.
            mock_web_services_api (MockVuforiaWebServicesAPI): An instance of a
                mock web services API.
        """
        self.routes: Set[Route] = ROUTES
        self.access_key: str = client_access_key
        self.secret_key: str = client_secret_key
        self.mock_web_services_api = mock_web_services_api

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
        invalid_type_error = (
            f"Invalid value '{max_num_results.decode()}' in form data "
            "part 'max_result'. "
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
                f'Integer out of range ({max_num_results_int}) in form data '
                "part 'max_result'. "
                'Accepted range is from 1 to 50 (inclusive).'
            )
            return out_of_range_error

        [include_target_data] = parsed.get('include_target_data', [b'top'])
        allowed_included_target_data = {b'top', b'all', b'none'}
        if include_target_data not in allowed_included_target_data:
            unexpected_target_data_message = (
                f"Invalid value '{include_target_data.decode()}' in form data "
                "part 'include_target_data'. "
                "Expecting one of the (unquoted) string values 'all', 'none' "
                "or 'top'."
            )
            context.status_code = codes.BAD_REQUEST
            return unexpected_target_data_message

        results: List[Dict[str, Any]] = []
        [image] = parsed['image']
        for target in self.mock_web_services_api.targets:
            if target.image.getvalue() == image:
                target_timestamp = int(target.last_modified_date.timestamp())
                target_data = {
                    'target_timestamp': target_timestamp,
                    'name': target.name,
                    'application_metadata': None,
                }
                result = {
                    'target_id': target.target_id,
                    'target_data': target_data,
                }
                results.append(result)

        body = {
            'result_code': ResultCodes.SUCCESS.value,
            'results': results,
            'query_id': uuid.uuid4().hex,
        }

        value = json_dump(body)
        return value
