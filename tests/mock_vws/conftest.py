"""
Configuration, plugins and fixtures for `pytest`.
"""

import base64
import bitmath
import io
import sys
import os
import uuid
# This is used in a type hint which linters not pick up on.
from typing import Any  # noqa: F401 pylint: disable=unused-import
from typing import Generator

import pytest
import requests
from _pytest.fixtures import SubRequest
from PIL import Image
from requests import codes
from requests_mock import DELETE, GET, POST, PUT
from retrying import retry

from common.constants import ResultCodes
from mock_vws import MockVWS
from tests.mock_vws.utils import Endpoint, add_target_to_vws
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


def _image_file(file_format: str, color_space: str) -> io.BytesIO:
    """
    Return an image file in the given format and color space.

    Args:
        file_format: See
            http://pillow.readthedocs.io/en/3.1.x/handbook/image-file-formats.html
        color_space: One of "L", "RGB", or "CMYK". "L" means greyscale.
    """
    image_buffer = io.BytesIO()
    width = 1
    height = 1
    image = Image.new(color_space, (width, height))
    image.save(image_buffer, file_format)
    image_buffer.seek(0)
    return image_buffer


@pytest.fixture
def png_rgb() -> io.BytesIO:
    """
    Return a PNG file in the RGB color space.
    """
    return _image_file(file_format='PNG', color_space='RGB')


@pytest.fixture()
def png_large(png_rgb) -> io.BytesIO:
    """
    Return a PNG file 2 MB in size.
    """
    png_size = len(png_rgb.getbuffer())
    max_size = bitmath.MiB(2.1)
    filler_length = max_size - png_size
    filler_data = b'\x00' * int(filler_length)
    original_data = png_rgb.getvalue()
    long_data = original_data.replace(b'IEND', filler_data + b'IEND')
    png = io.BytesIO(long_data)
    return png


@pytest.fixture()
def png_too_large(png_large) -> io.BytesIO:
    """
    Return a PNG file just over 2 MB in size.
    """
    original_data = png_large.getvalue()
    long_data = original_data.replace(b'IEND', 'b\x00' + b'IEND')
    png = io.BytesIO(long_data)
    return png


@pytest.fixture
def png_greyscale() -> io.BytesIO:
    """
    Return a PNG file in the greyscale color space.
    """
    return _image_file(file_format='PNG', color_space='L')


@pytest.fixture
def jpeg_cmyk() -> io.BytesIO:
    """
    Return a PNG file in the CMYK color space.
    """
    return _image_file(file_format='JPEG', color_space='CMYK')


@pytest.fixture
def jpeg_rgb() -> io.BytesIO:
    """
    Return a JPEG file in the RGB color space.
    """
    return _image_file(file_format='JPEG', color_space='RGB')


@pytest.fixture
def tiff_rgb() -> io.BytesIO:
    """
    Return a TIFF file in the RGB color space.

    This is given as an option which is not supported by Vuforia as Vuforia
    supports only JPEG and PNG files.
    """
    return _image_file(file_format='TIFF', color_space='RGB')


@pytest.fixture(params=[
    # 'png_rgb',
    # 'jpeg_rgb',
    # 'png_greyscale',
    'png_large',
])
def image_file(request: SubRequest) -> io.BytesIO:
    """
    Return an image file which is expected to work on Vuforia.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    # 'tiff_rgb',
    # 'jpeg_cmyk',
    'png_too_large',
], ids=[
    # 'Invalid format',
    # 'Invalid color space',
    'Too large',
])
def bad_image_file(request: SubRequest) -> io.BytesIO:
    """
    Return an image file which is not expected to work on Vuforia.
    """
    return request.getfixturevalue(request.param)


@retry(
    stop_max_delay=2 * 60 * 1000,
    wait_fixed=3 * 1000,
)
def _delete_target(vuforia_server_credentials: VuforiaServerCredentials,
                   target: str) -> None:
    """
    Delete a given target.

    Args:
        vuforia_server_credentials: The credentials to the Vuforia target
            database to delete the target in.
        target: The ID of the target to delete.

    Raises:
        AssertionError: The deletion was not a success.
    """
    date = rfc_1123_date()

    authorization_string = authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=DELETE,
        content=b'',
        content_type='',
        date=date,
        request_path='/targets/{target}'.format(target=target),
    )

    headers = {
        "Authorization": authorization_string,
        "Date": date,
    }

    response = requests.request(
        method=DELETE,
        url='https://vws.vuforia.com/targets/{target}'.format(target=target),
        headers=headers,
        data=b'',
    )

    result_code = response.json()['result_code']
    error_message = (
        'Deleting a target failed. '
        'The result code returned was: {result_code}. '
        'Perhaps wait and try again. '
        'However, sometimes targets get stuck on Vuforia, '
        'and a new testing database is required.'
    ).format(result_code=result_code)

    acceptable_results = (
        ResultCodes.SUCCESS.value,
        ResultCodes.UNKNOWN_TARGET.value,
    )
    assert result_code in acceptable_results, error_message


def _delete_all_targets(vuforia_server_credentials: VuforiaServerCredentials,
                        ) -> None:
    """
    Delete all targets.

    Args:
        vuforia_server_credentials: The credentials to the Vuforia target
            database to delete all targets in.
    """
    date = rfc_1123_date()

    authorization_string = authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        content_type='',
        date=date,
        request_path='/targets',
    )

    headers = {
        "Authorization": authorization_string,
        "Date": date,
    }

    response = requests.request(
        method=GET,
        url='https://vws.vuforia.com/targets',
        headers=headers,
        data=b'',
    )
    targets = response.json()['results']

    for target in targets:
        _delete_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target=target,
        )


@pytest.fixture()
def target_id(
    png_rgb: io.BytesIO,  # pylint: disable=redefined-outer-name
    vuforia_server_credentials: VuforiaServerCredentials,
) -> None:
    """
    The target ID of a target in the database.
    """
    image_data = png_rgb.read()
    image_data_encoded = base64.b64encode(image_data).decode('ascii')

    data = {
        'name': 'example',
        'width': 1,
        'image': image_data_encoded,
    }

    response = add_target_to_vws(
        vuforia_server_credentials=vuforia_server_credentials,
        data=data,
        content_type='application/json',
    )

    return response.json()['target_id']


@pytest.fixture(params=[True, False], ids=['Real Vuforia', 'Mock Vuforia'])
def verify_mock_vuforia(request: SubRequest,
                        vuforia_server_credentials: VuforiaServerCredentials,
                        ) -> Generator:
    """
    Using this fixture in a test will make it run twice. Once with the real
    Vuforia, and once with the mock.

    This is useful for verifying the mock.
    """
    skip_real = os.getenv('SKIP_REAL') == '1'
    skip_mock = os.getenv('SKIP_MOCK') == '1'

    use_real_vuforia = request.param

    if use_real_vuforia and skip_real:  # pragma: no cover
        pytest.skip()

    if not use_real_vuforia and skip_mock:  # pragma: no cover
        pytest.skip()

    if use_real_vuforia:
        _delete_all_targets(
            vuforia_server_credentials=vuforia_server_credentials,
        )
        yield
    else:
        with MockVWS():
            yield


@pytest.fixture()
def add_target() -> Endpoint:
    """
    Return details of the endpoint for adding a target.
    """
    data = {}  # type: Dict[str, Any]
    return Endpoint(
        example_path='/targets',
        method=POST,
        # We expect a bad request error because we have not given the required
        # JSON body elements.
        successful_headers_status_code=codes.BAD_REQUEST,
        successful_headers_result_code=ResultCodes.FAIL,
        content_type='application/json',
        content=bytes(str(data), encoding='utf-8'),
    )


@pytest.fixture()
def delete_target() -> Endpoint:
    """
    Return details of the endpoint for deleting a target.
    """
    example_path = '/targets/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=DELETE,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def database_summary() -> Endpoint:
    """
    Return details of the endpoint for getting details about the database.
    """
    return Endpoint(
        example_path='/summary',
        method=GET,
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def get_duplicates() -> Endpoint:
    """
    Return details of the endpoint for getting potential duplicates of a
    target.
    """
    example_path = '/duplicates/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=GET,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def get_target() -> Endpoint:
    """
    Return details of the endpoint for getting details of a target.
    """
    example_path = '/targets/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=GET,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def target_list() -> Endpoint:
    """
    Return details of the endpoint for getting a list of targets.
    """
    return Endpoint(
        example_path='/targets',
        method=GET,
        successful_headers_status_code=codes.OK,
        successful_headers_result_code=ResultCodes.SUCCESS,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def target_summary() -> Endpoint:
    """
    Return details of the endpoint for getting a summary report of a target.
    """
    example_path = '/summary/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=GET,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type=None,
        content=b'',
    )


@pytest.fixture()
def update_target() -> Endpoint:
    """
    Return details of the endpoint for updating a target.
    """
    data = {}  # type: Dict[str, Any]
    example_path = '/targets/{target_id}'.format(target_id=uuid.uuid4().hex)
    return Endpoint(
        example_path=example_path,
        method=PUT,
        successful_headers_status_code=codes.NOT_FOUND,
        successful_headers_result_code=ResultCodes.UNKNOWN_TARGET,
        content_type='application/json',
        content=bytes(str(data), encoding='utf-8'),
    )


@pytest.fixture(params=[
    'delete_target',
    'get_target',
    'get_duplicates',
    'target_summary',
    'update_target',
])
def endpoint_which_takes_target_id(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which takes a target ID in the path.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    'database_summary',
    'delete_target',
    'get_duplicates',
    'get_target',
    'target_list',
    'target_summary',
])
def endpoint_no_data(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which does not take any JSON data.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    'add_target',
    'update_target',
])
def endpoint_which_takes_data(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which takes JSON data.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[
    'add_target',
    'database_summary',
    'delete_target',
    'get_duplicates',
    'get_target',
    'target_list',
    'target_summary',
    'update_target',
])
def endpoint(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint.
    """
    return request.getfixturevalue(request.param)
