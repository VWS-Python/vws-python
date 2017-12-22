"""
Configuration, plugins and fixtures for `pytest`.
"""

import base64
import io
import os
import random
import uuid
from typing import Any, Dict, Generator

import pytest
from _pytest.fixtures import SubRequest
from PIL import Image
from requests import codes
from requests_mock import DELETE, GET, POST, PUT
from retrying import retry

from common.constants import ResultCodes
from mock_vws import MockVWS, States
from tests.mock_vws.utils import Endpoint, add_target_to_vws
from tests.utils import VuforiaServerCredentials
from vws._request_utils import target_api_request


def _image_file(
    file_format: str, color_space: str, width: int, height: int
) -> io.BytesIO:
    """
    Return an image file in the given format and color space.

    The image file is filled with randomly colored pixels.

    Args:
        file_format: See
            http://pillow.readthedocs.io/en/3.1.x/handbook/image-file-formats.html
        color_space: One of "L", "RGB", or "CMYK". "L" means greyscale.
        width: The width, in pixels of the image.
        height: The width, in pixels of the image.
    """
    image_buffer = io.BytesIO()
    image = Image.new(color_space, (width, height))
    pixels = image.load()
    for i in range(height):
        for j in range(width):
            red = random.randint(0, 255)
            green = random.randint(0, 255)
            blue = random.randint(0, 255)
            if color_space != 'L':
                pixels[i, j] = (red, green, blue)
    image.save(image_buffer, file_format)
    image_buffer.seek(0)
    return image_buffer


@pytest.fixture
def png_rgb_success() -> io.BytesIO:
    """
    Return a PNG file in the RGB color space which is expected to have a
    'success' status when added to a target.
    """
    return _image_file(file_format='PNG', color_space='RGB', width=5, height=5)


@pytest.fixture
def png_rgb() -> io.BytesIO:
    """
    Return a 1x1 PNG file in the RGB color space.
    """
    return _image_file(file_format='PNG', color_space='RGB', width=1, height=1)


@pytest.fixture
def png_greyscale() -> io.BytesIO:
    """
    Return a 1x1 PNG file in the greyscale color space.
    """
    return _image_file(file_format='PNG', color_space='L', width=1, height=1)


@pytest.fixture()
def png_large(
    png_rgb: io.BytesIO,  # pylint: disable=redefined-outer-name
) -> io.BytesIO:
    """
    Return a PNG file of the maximum allowed file size.

    https://library.vuforia.com/articles/Training/Cloud-Recognition-Guide
    describes that the maximum allowed file size of an image is 2 MB.
    However, tests using this fixture demonstrate that the maximum allowed
    size is actually slightly greater than that.
    """
    png_size = len(png_rgb.getbuffer())
    max_size = 2359293
    filler_length = max_size - png_size
    filler_data = b'\x00' * int(filler_length)
    original_data = png_rgb.getvalue()
    longer_data = original_data.replace(b'IEND', filler_data + b'IEND')
    png = io.BytesIO(longer_data)
    return png


@pytest.fixture
def jpeg_cmyk() -> io.BytesIO:
    """
    Return a 1x1 JPEG file in the CMYK color space.
    """
    return _image_file(
        file_format='JPEG',
        color_space='CMYK',
        width=1,
        height=1,
    )


@pytest.fixture
def jpeg_rgb() -> io.BytesIO:
    """
    Return a 1x1 JPEG file in the RGB color space.
    """
    return _image_file(
        file_format='JPEG',
        color_space='RGB',
        width=1,
        height=1,
    )


@pytest.fixture
def tiff_rgb() -> io.BytesIO:
    """
    Return a 1x1 TIFF file in the RGB color space.

    This is given as an option which is not supported by Vuforia as Vuforia
    supports only JPEG and PNG files.
    """
    return _image_file(
        file_format='TIFF',
        color_space='RGB',
        width=1,
        height=1,
    )


@pytest.fixture(params=['png_rgb', 'jpeg_rgb', 'png_greyscale', 'png_large'])
def image_file(request: SubRequest) -> io.BytesIO:
    """
    Return an image file which is expected to work on Vuforia.

    "work" means that this will be added as a target. However, this may or may
    not result in target with a 'success' status.
    """
    file_bytes_io: io.BytesIO = request.getfixturevalue(request.param)
    return file_bytes_io


@pytest.fixture(params=['tiff_rgb', 'jpeg_cmyk'])
def bad_image_file(request: SubRequest) -> io.BytesIO:
    """
    Return an image file which is expected to work on Vuforia which is
    expected to cause a `BadImage` result when an attempt is made to add it to
    the target database.
    """
    file_bytes_io: io.BytesIO = request.getfixturevalue(request.param)
    return file_bytes_io


@retry(
    stop_max_delay=2 * 60 * 1000,
    wait_fixed=3 * 1000,
)
def _delete_target(
    vuforia_server_credentials: VuforiaServerCredentials,
    target: str,
) -> None:
    """
    Delete a given target.

    Args:
        vuforia_server_credentials: The credentials to the Vuforia target
            database to delete the target in.
        target: The ID of the target to delete.

    Raises:
        AssertionError: The deletion was not a success.
    """
    response = target_api_request(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=DELETE,
        content=b'',
        request_path='/targets/{target}'.format(target=target),
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


def _delete_all_targets(
    vuforia_server_credentials: VuforiaServerCredentials,
) -> None:
    """
    Delete all targets.

    Args:
        vuforia_server_credentials: The credentials to the Vuforia target
            database to delete all targets in.
    """
    response = target_api_request(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=GET,
        content=b'',
        request_path='/targets',
    )

    if 'results' not in response.json():  # pragma: no cover
        print('Results not found.')
        print('Response is:')
        print(response.json())

    targets = response.json()['results']

    for target in targets:
        _delete_target(
            vuforia_server_credentials=vuforia_server_credentials,
            target=target,
        )


@pytest.fixture()
def target_id(
    png_rgb_success: io.BytesIO,  # pylint: disable=redefined-outer-name
    vuforia_server_credentials: VuforiaServerCredentials,
) -> str:
    """
    Return the target ID of a target in the database.

    The target is one which will have a 'success' status when processed.
    """
    image_data = png_rgb_success.read()
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

    return str(response.json()['target_id'])


@pytest.fixture(params=[True, False], ids=['Real Vuforia', 'Mock Vuforia'])
def verify_mock_vuforia(
    request: SubRequest,
    vuforia_server_credentials: VuforiaServerCredentials,
) -> Generator:
    """
    Test functions which use this fixture are run twice. Once with the real
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
        with MockVWS(
            database_name=vuforia_server_credentials.database_name,
            access_key=vuforia_server_credentials.access_key.decode('ascii'),
            secret_key=vuforia_server_credentials.secret_key.decode('ascii'),
        ):
            yield


@pytest.fixture(params=[True, False], ids=['Real Vuforia', 'Mock Vuforia'])
def verify_mock_vuforia_inactive(
    request: SubRequest,
    inactive_server_credentials: VuforiaServerCredentials,
) -> Generator:
    """
    Test functions which use this fixture are run twice. Once with the real
    Vuforia in an inactive state, and once with the mock in an inactive state.

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
        yield
    else:
        with MockVWS(
            state=States.PROJECT_INACTIVE,
            database_name=inactive_server_credentials.database_name,
            access_key=inactive_server_credentials.access_key.decode('ascii'),
            secret_key=inactive_server_credentials.secret_key.decode('ascii'),
        ):
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


@pytest.fixture(
    params=[
        'delete_target',
        'get_target',
        'get_duplicates',
        'target_summary',
        'update_target',
    ]
)
def endpoint_which_takes_target_id(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which takes a target ID in the path.
    """
    endpoint_fixture = request.getfixturevalue(request.param)  # type: Endpoint
    return endpoint_fixture


@pytest.fixture(
    params=[
        'database_summary',
        'delete_target',
        'get_duplicates',
        'get_target',
        'target_list',
        'target_summary',
    ]
)
def endpoint_no_data(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which does not take any JSON data.
    """
    endpoint_fixture = request.getfixturevalue(request.param)  # type: Endpoint
    return endpoint_fixture


@pytest.fixture(params=[
    'add_target',
    'update_target',
])
def endpoint_which_takes_data(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint which takes JSON data.
    """
    endpoint_fixture = request.getfixturevalue(request.param)  # type: Endpoint
    return endpoint_fixture


@pytest.fixture(
    params=[
        'add_target',
        'database_summary',
        'delete_target',
        'get_duplicates',
        'get_target',
        'target_list',
        'target_summary',
        'update_target',
    ]
)
def endpoint(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint.
    """
    endpoint_fixture = request.getfixturevalue(request.param)  # type: Endpoint
    return endpoint_fixture
