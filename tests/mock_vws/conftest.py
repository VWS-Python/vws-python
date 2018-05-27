"""
Configuration, plugins and fixtures for `pytest`.
"""

import base64
import io
import logging
import os
from typing import Generator

import pytest
from _pytest.fixtures import SubRequest

from mock_vws import MockVWS, States
from tests.mock_vws.utils import (
    Endpoint,
    add_target_to_vws,
    delete_target,
    list_targets,
    update_target,
    wait_for_target_processed,
)
from tests.mock_vws.utils.authorization import VuforiaDatabaseKeys

pytest_plugins = [  # pylint: disable=invalid-name
    'tests.mock_vws.fixtures.prepared_requests',
    'tests.mock_vws.fixtures.images',
    'tests.mock_vws.fixtures.credentials',
]

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def _delete_all_targets(database_keys: VuforiaDatabaseKeys) -> None:
    """
    Delete all targets.

    Args:
        database_keys: The credentials to the Vuforia target database to delete
            all targets in.
    """
    response = list_targets(vuforia_database_keys=database_keys)

    if 'results' not in response.json():  # pragma: no cover
        message = f'Results not found.\nResponse is: {response.json()}'
        LOGGER.debug(message)

    targets = response.json()['results']

    for target in targets:
        wait_for_target_processed(
            vuforia_database_keys=database_keys,
            target_id=target,
        )
        update_target(
            vuforia_database_keys=database_keys,
            data={'active_flag': False},
            target_id=target,
        )
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
            client_access_key=vuforia_database_keys.client_access_key.
            decode('ascii'),
            client_secret_key=vuforia_database_keys.client_secret_key.
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
        '_query',
    ],
)
def endpoint(request: SubRequest) -> Endpoint:
    """
    Return details of an endpoint for the Target API or the Query API.
    """
    endpoint_fixture: Endpoint = request.getfixturevalue(request.param)
    return endpoint_fixture
