"""Setup for Sybil."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from doctest import ELLIPSIS

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuMarkDatabase
from mock_vws.target import VuMarkTarget
from sybil import Sybil
from sybil.parsers.rest import (
    ClearNamespaceParser,
    DocTestParser,
    PythonCodeBlockParser,
)


@pytest.fixture(name="mock_vws")
def fixture_mock_vws(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None]:
    """Yield a mock VWS.

    The keys used here match the keys in the documentation.
    """
    server_access_key = uuid.uuid4().hex
    server_secret_key = uuid.uuid4().hex
    target = VuMarkTarget(name="example-template")

    database = VuMarkDatabase(
        server_access_key=server_access_key,
        server_secret_key=server_secret_key,
        vumark_targets={target},
    )

    monkeypatch.setenv(name="VWS_SERVER_ACCESS_KEY", value=server_access_key)
    monkeypatch.setenv(name="VWS_SERVER_SECRET_KEY", value=server_secret_key)
    monkeypatch.setenv(name="VUMARK_TARGET_ID", value=target.target_id)
    # The mock accepts one hard-coded pair of Model Target Web API OAuth2
    # credentials, which it does not expose.
    monkeypatch.setenv(
        name="VWS_MODEL_TARGET_CLIENT_ID",
        value="client-id",
    )
    monkeypatch.setenv(
        name="VWS_MODEL_TARGET_CLIENT_SECRET",
        value="client-secret",
    )
    # We use a low processing time so that tests run quickly.
    with MockVWS(processing_time_seconds=0.2) as mock:
        mock.add_vumark_database(vumark_database=database)
        yield


pytest_collect_file = Sybil(
    parsers=[
        ClearNamespaceParser(),
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=["*.rst", "*.py"],
    fixtures=["mock_vws"],
).pytest()
