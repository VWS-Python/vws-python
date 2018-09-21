"""
Tests for various exceptions.
"""

import pytest
from requests import codes

from vws import VWS
from vws.exceptions import UnknownTarget


def test_invalid_given_id(client: VWS) -> None:
    """
    Giving an invalid ID to a helper which requires a target ID to be given
    causes an ``UnknownTarget`` exception to be raised.
    """
    with pytest.raises(UnknownTarget) as exc:
        client.delete_target(target_id='x')
    assert exc.value.response.status_code == codes.NOT_FOUND


def test_request_quota_reached() -> None:
    """
    See https://github.com/adamtheturtle/vws-python/issues/822 for writing
    this test.
    """
