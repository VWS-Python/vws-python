"""Setup for Sybil."""

import io
import sys
from collections.abc import Generator
from doctest import ELLIPSIS
from pathlib import Path

import pytest
from beartype import beartype
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from sybil import Sybil
from sybil.parsers.rest import (
    ClearNamespaceParser,
    CodeBlockParser,
    DocTestParser,
    PythonCodeBlockParser,
)
from sybil_extras.evaluators.shell_evaluator import ShellCommandEvaluator


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """
    Apply the beartype decorator to all collected test functions.
    """
    for item in items:
        if isinstance(item, pytest.Function):
            item.obj = beartype(obj=item.obj)


@pytest.fixture
def make_image_file(
    high_quality_image: io.BytesIO,
) -> Generator[None, None, None]:
    """
    Make an image file available in the test directory.
    The path of this file matches the path in the documentation.
    """
    new_image = Path("high_quality_image.jpg")
    buffer = high_quality_image.getvalue()
    new_image.write_bytes(data=buffer)
    yield
    new_image.unlink()


@pytest.fixture
def mock_vws() -> Generator[None, None, None]:
    """
    Yield a mock VWS.

    The keys used here match the keys in the documentation.
    """
    database = VuforiaDatabase(
        server_access_key="[server-access-key]",
        server_secret_key="[server-secret-key]",
        client_access_key="[client-access-key]",
        client_secret_key="[client-secret-key]",
    )
    # We use a low processing time so that tests run quickly.
    with MockVWS(processing_time_seconds=0.2) as mock:
        mock.add_database(database=database)
        yield


pytest_collect_file = Sybil(
    parsers=[
        ClearNamespaceParser(),
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=["*.rst", "*.py"],
).pytest()

run_code_sybil = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=["*.rst", "*.py"],
    fixtures=["make_image_file", "mock_vws"],
)

pytest_sybil = Sybil(
    parsers=[
        CodeBlockParser(
            language="python",
            evaluator=ShellCommandEvaluator(
                args=[sys.executable, "-m", "pytest"],
                tempfile_suffixes=[".py"],
                pad_file=True,
                write_to_file=False,
            ),
        ),
    ],
    patterns=["*.rst"],
    fixtures=["make_image_file"],
)

sybils = run_code_sybil + pytest_sybil

pytest_collect_file = sybils.pytest()
