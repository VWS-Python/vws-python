"""
Tests for passing invalid target IDs to helpers which require a target ID to
be given.
"""

from typing import Any, Callable, Dict, Union

import pytest
from _pytest.fixtures import SubRequest
from requests import codes

from vws import VWS
from vws.exceptions import UnknownTarget


@pytest.fixture()
def _delete_target(client: VWS) -> Callable[[str], None]:
    return client.delete_target


@pytest.fixture()
def _get_target_record(client: VWS,
                       ) -> Callable[[str], Dict[str, Union[str, int]]]:
    return client.get_target_record


@pytest.fixture()
def _wait_for_target_processed(client: VWS) -> Any:
    return client.wait_for_target_processed


@pytest.fixture()
def _get_target_summary_report(
    client: VWS,
) -> Callable[[str], Dict[str, Union[str, int]]]:
    return client.get_target_summary_report


@pytest.mark.parametrize(
    'fixture',
    [
        '_delete_target',
        '_get_target_record',
        '_wait_for_target_processed',
        '_get_target_summary_report',
    ],
)
def test_invalid_given_id(
    fixture: Callable[[str], None],
    request: SubRequest,
) -> None:
    """
    Giving an invalid ID to a helper which requires a target ID to be given
    causes an ``UnknownTarget`` exception to be raised.
    """
    func = request.getfixturevalue(fixture)
    with pytest.raises(UnknownTarget) as exc:
        func(target_id='x')
    assert exc.value.response.status_code == codes.NOT_FOUND
