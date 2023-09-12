"""Setup for Sybil."""

from doctest import ELLIPSIS

from sybil import Sybil  # pyright: ignore[reportMissingTypeStubs]
from sybil.parsers.rest import (  # pyright: ignore[reportMissingTypeStubs]
    ClearNamespaceParser,
    DocTestParser,
    PythonCodeBlockParser,
)

pytest_collect_file = Sybil(  # pyright: ignore[reportUnknownVariableType]
    parsers=[
        ClearNamespaceParser(),
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=["*.rst", "*.py"],
).pytest()
