"""
Tests for passing invalid target IDs to helpers which require a target ID to
be given.
"""

from typing import Callable

import pytest
from _pytest.fixtures import SubRequest

from vws import VWS
from vws.exceptions import UnknownTarget


@pytest.fixture()
def _delete_target(client: VWS) -> Callable[[str], None]:
    return client.delete_target


@pytest.mark.parametrize('fixture', ['_delete_target'])
def test_invalid_given_id(fixture: Callable[[str], None], request: SubRequest,) -> None:
    """
    Giving an invalid ID to a helper which requires a target ID to be given
    causes an ``UnknownTarget`` exception to be raised.
    """
    func = request.getfixturevalue(fixture)
    with pytest.raises(UnknownTarget):
        func(target_id='x')
