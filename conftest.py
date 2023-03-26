"""Setup for Sybil."""

from doctest import ELLIPSIS

from sybil import Sybil
from sybil.parsers.rest import (
    ClearNamespaceParser,
    DocTestParser,
    PythonCodeBlockParser,
)

pytest_collect_file = Sybil(
    parsers=[
        ClearNamespaceParser(),
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),
    ],
    patterns=["*.rst", "*.py"],
).pytest()
