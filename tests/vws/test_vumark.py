"""Tests for `VWS` vumark."""

from __future__ import annotations

import pytest

# pytest-beartype resolves fixture annotations at runtime.
from vws import VuMarkService  # noqa: TC001
from vws.vumark_accept import VuMarkAccept


@pytest.mark.parametrize(
    argnames=("accept", "expected_prefix"),
    argvalues=[
        pytest.param(VuMarkAccept.PNG, b"\x89PNG\r\n\x1a\n", id="png"),
        pytest.param(VuMarkAccept.SVG, b"<", id="svg"),
        pytest.param(VuMarkAccept.PDF, b"%PDF", id="pdf"),
    ],
)
def test_generate_vumark_instance(
    *,
    vumark_service_client: VuMarkService,
    vumark_target_id: str,
    accept: VuMarkAccept,
    expected_prefix: bytes,
) -> None:
    """The returned bytes match the requested format."""
    result = vumark_service_client.generate_vumark_instance(
        target_id=vumark_target_id,
        instance_id="12345",
        accept=accept,
    )
    assert result.startswith(expected_prefix)
