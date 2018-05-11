"""
Configuration, plugins and fixtures for `pytest`.
"""

import base64
import io
import os
from typing import Generator

import pytest
from _pytest.fixtures import SubRequest
from requests_mock import GET

from mock_vws import MockVWS, States
from tests.mock_vws.utils import (
    TargetAPIEndpoint,
    VuforiaDatabaseKeys,
    add_target_to_vws,
    delete_target,
    target_api_request,
)

pytest_plugins = [  # pylint: disable=invalid-name
    'tests.mock_vws.fixtures.prepared_requests',
    'tests.mock_vws.fixtures.images',
    'tests.mock_vws.fixtures.credentials',
]


def _delete_all_targets(database_keys: VuforiaDatabaseKeys) -> None:
    """
    Delete all targets.

    Args:
        database_keys: The credentials to the Vuforia target database to delete
            all targets in.
    """
    response = target_api_request(
        server_access_key=database_keys.server_access_key,
        server_secret_key=database_keys.server_secret_key,
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
        delete_target(vuforia_database_keys=database_keys, target_id=target)


@pytest.fixture()
def target_id(
    png_rgb_success: io.BytesIO,
    vuforia_database_keys: VuforiaDatabaseKeys,
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
        vuforia_database_keys=vuforia_database_keys,
        data=data,
        content_type='application/json',
    )

    return str(response.json()['target_id'])


@pytest.fixture(params=[True, False], ids=['Real Vuforia', 'Mock Vuforia'])
def verify_mock_vuforia(
    request: SubRequest,
    vuforia_database_keys: VuforiaDatabaseKeys,
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
        _delete_all_targets(database_keys=vuforia_database_keys)
        yield
    else:
        with MockVWS(
            database_name=vuforia_database_keys.database_name,
            server_access_key=vuforia_database_keys.server_access_key.
            decode('ascii'),
            server_secret_key=vuforia_database_keys.server_secret_key.
            decode('ascii'),
            processing_time_seconds=0.1,
        ):
            yield


@pytest.fixture(params=[True, False], ids=['Real Vuforia', 'Mock Vuforia'])
def verify_mock_vuforia_inactive(
    request: SubRequest,
    inactive_database_keys: VuforiaDatabaseKeys,
) -> Generator:
    """
    Test functions which use this fixture are run twice. Once with the real
    Vuforia in an inactive state, and once with the mock in an inactive state.

    This is useful for verifying the mock.

    To create an inactive project, delete the license key associated with a
    database.
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
            database_name=inactive_database_keys.database_name,
            server_access_key=inactive_database_keys.server_access_key.
            decode('ascii'),
            server_secret_key=inactive_database_keys.server_secret_key.
            decode('ascii'),
        ):
            yield


@pytest.fixture(
    params=[
        '_add_target',
        '_database_summary',
        '_delete_target',
        '_get_duplicates',
        '_get_target',
        '_target_list',
        '_target_summary',
        '_update_target',
    ],
)
def endpoint(request: SubRequest) -> TargetAPIEndpoint:
    """
    Return details of an endpoint.
    """
    endpoint_fixture: TargetAPIEndpoint = request.getfixturevalue(
        request.param,
    )
    return endpoint_fixture


@pytest.fixture(
    params=[
        '_query',
    ],
)
def query_endpoint(request: SubRequest) -> TargetAPIEndpoint:
    """
    Return details of the query endpoint.
    """
    endpoint_fixture: TargetAPIEndpoint = request.getfixturevalue(
        request.param,
    )
    return endpoint_fixture
