"""
Input validators to use in the mock.
"""

import base64
import binascii
import io
import json
import numbers
import uuid
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import Any, Callable, Dict, Set, Tuple

import wrapt
from PIL import Image
from requests import codes
from requests_mock import POST, PUT
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from common.constants import ResultCodes
from vws._request_utils import authorization_header


@wrapt.decorator
def validate_active_flag(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the active flag data given to the endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response with a FAIL result code if there is
        active flag data given to the endpoint which is not either a Boolean or
        NULL.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    if 'active_flag' not in request.json():
        return wrapped(*args, **kwargs)

    active_flag = request.json().get('active_flag')

    if active_flag is None or isinstance(active_flag, bool):
        return wrapped(*args, **kwargs)

    context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
    body = {
        'transaction_id': uuid.uuid4().hex,
        'result_code': ResultCodes.FAIL.value,
    }  # type: Dict[str, str]
    return json.dumps(body)


@wrapt.decorator
def validate_not_invalid_json(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that there is either no JSON given or the JSON given is valid.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNAUTHORIZED` response if there is data given to the database
        summary endpoint.
        A `BAD_REQUEST` response with a FAIL result code if there is invalid
        JSON given to a POST or PUT request.
        A `BAD_REQUEST` with empty text if there is data given to another
        request type.
    """
    request, context = args

    if request.text is None:
        return wrapped(*args, **kwargs)

    if request.path == '/summary':
        context.status_code = codes.UNAUTHORIZED  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.AUTHENTICATION_FAILURE.value,
        }
        return json.dumps(body)

    if request.method not in (POST, PUT):
        context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
        context.headers.pop('Content-Type')
        return ''

    try:
        request.json()
    except JSONDecodeError:
        context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_auth_header_exists(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
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
        context.status_code = codes.UNAUTHORIZED  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.AUTHENTICATION_FAILURE.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_authorization(
    wrapped: Callable[..., str],
    instance: Any,
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
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
        context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_date(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the date header given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response if the date is not given, or is in the wrong
        format.
        A `FORBIDDEN` response if the date is out of range.
    """
    request, context = args

    try:
        date_from_header = datetime.strptime(
            request.headers['Date'],
            '%a, %d %b %Y %H:%M:%S GMT',
        )
    except (KeyError, ValueError):
        context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    time_difference = datetime.now() - date_from_header
    maximum_time_difference = timedelta(minutes=5)

    if abs(time_difference) >= maximum_time_difference:
        context.status_code = codes.FORBIDDEN  # pylint: disable=no-member

        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.REQUEST_TIME_TOO_SKEWED.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_width(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the width argument given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response if the width is given and is not a positive
        number.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    if 'width' not in request.json():
        return wrapped(*args, **kwargs)

    width = request.json().get('width')

    width_is_number = isinstance(width, numbers.Number)
    width_positive = width_is_number and width > 0

    if not width_positive:
        context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_name(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the name argument given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        A `BAD_REQUEST` response if the name is given and is not between 1 and
        64 characters in length.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    if 'name' not in request.json():
        return wrapped(*args, **kwargs)

    name = request.json().get('name')

    name_is_string = isinstance(name, str)
    name_valid_length = name_is_string and 0 < len(name) < 65

    if not name_valid_length:
        context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_image_format(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the format of the image given to a VWS endpoint.

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

    if not request.text:
        return wrapped(*args, **kwargs)

    image = request.json().get('image')

    if image is None:
        return wrapped(*args, **kwargs)

    decoded = base64.b64decode(image)
    image_file = io.BytesIO(decoded)
    pil_image = Image.open(image_file)

    if pil_image.format in ('PNG', 'JPEG'):
        return wrapped(*args, **kwargs)

    context.status_code = codes.UNPROCESSABLE_ENTITY  # noqa: E501 pylint: disable=no-member
    body = {
        'transaction_id': uuid.uuid4().hex,
        'result_code': ResultCodes.BAD_IMAGE.value,
    }
    return json.dumps(body)


@wrapt.decorator
def validate_image_color_space(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the color space of the image given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNPROCESSABLE_ENTITY` response if the image is given and is not
        in either the RGB or greyscale color space.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    image = request.json().get('image')

    if image is None:
        return wrapped(*args, **kwargs)

    decoded = base64.b64decode(image)
    image_file = io.BytesIO(decoded)
    pil_image = Image.open(image_file)

    if pil_image.mode in ('L', 'RGB'):
        return wrapped(*args, **kwargs)

    context.status_code = codes.UNPROCESSABLE_ENTITY  # noqa: E501 pylint: disable=no-member
    body = {
        'transaction_id': uuid.uuid4().hex,
        'result_code': ResultCodes.BAD_IMAGE.value,
    }
    return json.dumps(body)


@wrapt.decorator
def validate_image_size(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate the file size of the image given to a VWS endpoint.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNPROCESSABLE_ENTITY` response if the image is given and is not
        under a certain file size threshold.
        This threshold is documented as being 2 MB but it is actually
        slightly larger. See the `png_large` fixture for more details.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    image = request.json().get('image')

    if image is None:
        return wrapped(*args, **kwargs)

    decoded = base64.b64decode(image)

    if len(decoded) <= 2359293:
        return wrapped(*args, **kwargs)

    context.status_code = codes.UNPROCESSABLE_ENTITY  # noqa: E501 pylint: disable=no-member
    body = {
        'transaction_id': uuid.uuid4().hex,
        'result_code': ResultCodes.IMAGE_TOO_LARGE.value,
    }
    return json.dumps(body)


@wrapt.decorator
def validate_image_is_image(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that the given image data is actually an image file.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNPROCESSABLE_ENTITY` response if image data is given and it is not
        an image file.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    image = request.json().get('image')

    if image is None:
        return wrapped(*args, **kwargs)

    decoded = base64.b64decode(image)
    image_file = io.BytesIO(decoded)

    try:
        Image.open(image_file)
    except OSError:
        context.status_code = codes.UNPROCESSABLE_ENTITY  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.BAD_IMAGE.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_image_encoding(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that the given image data can be base64 decoded.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNPROCESSABLE_ENTITY` response if image data is given and it cannot
        be base64 decoded.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    if 'image' not in request.json():
        return wrapped(*args, **kwargs)

    image = request.json().get('image')

    try:
        base64.b64decode(image)
    except binascii.Error:
        context.status_code = codes.UNPROCESSABLE_ENTITY  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_image_data_type(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that the given image data is a string.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `BAD_REQUEST` response if image data is given and it is not a
        string.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    if 'image' not in request.json():
        return wrapped(*args, **kwargs)

    image = request.json().get('image')

    if isinstance(image, str):
        return wrapped(*args, **kwargs)

    context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
    body = {
        'transaction_id': uuid.uuid4().hex,
        'result_code': ResultCodes.FAIL.value,
    }
    return json.dumps(body)


def validate_keys(
    mandatory_keys: Set[str],
    optional_keys: Set[str],
) -> Callable:
    """
    Args:
        mandatory_keys: Keys required by the endpoint.
        optional_keys: Keys which are not required by the endpoint but which
            are allowed.

    Returns:
        A wrapper function to validate that the keys given to the endpoint are
            all allowed and that the mandatory keys are given.
    """

    @wrapt.decorator
    def wrapper(
        wrapped: Callable[..., str],
        instance: Any,  # pylint: disable=unused-argument
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
            A `BAD_REQUEST` error if any keys are not allowed, or if any
            required keys are missing.
        """
        request, context = args
        allowed_keys = mandatory_keys.union(optional_keys)

        if request.text is None and not allowed_keys:
            return wrapped(*args, **kwargs)

        given_keys = set(request.json().keys())
        all_given_keys_allowed = given_keys.issubset(allowed_keys)
        all_mandatory_keys_given = mandatory_keys.issubset(given_keys)

        if all_given_keys_allowed and all_mandatory_keys_given:
            return wrapped(*args, **kwargs)

        context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapper


@wrapt.decorator
def validate_metadata_encoding(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that the given application metadata can be base64 decoded.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `UNPROCESSABLE_ENTITY` response if application metadata is given and
        it cannot be base64 decoded.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    if 'application_metadata' not in request.json():
        return wrapped(*args, **kwargs)

    application_metadata = request.json().get('application_metadata')

    if application_metadata is None:
        return wrapped(*args, **kwargs)

    try:
        base64.b64decode(application_metadata)
    except binascii.Error:
        context.status_code = codes.UNPROCESSABLE_ENTITY  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)

    return wrapped(*args, **kwargs)


@wrapt.decorator
def validate_metadata_type(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Validate that the given application metadata is a string or NULL.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
        An `BAD_REQUEST` response if application metadata is given and it is
        not a string or NULL.
    """
    request, context = args

    if not request.text:
        return wrapped(*args, **kwargs)

    if 'application_metadata' not in request.json():
        return wrapped(*args, **kwargs)

    application_metadata = request.json().get('application_metadata')

    if application_metadata is None or isinstance(application_metadata, str):
        return wrapped(*args, **kwargs)

    context.status_code = codes.BAD_REQUEST  # pylint: disable=no-member
    body = {
        'transaction_id': uuid.uuid4().hex,
        'result_code': ResultCodes.FAIL.value,
    }
    return json.dumps(body)
