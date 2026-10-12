"""Typed image cases and resources for API tests."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, BinaryIO, Literal

from beartype import beartype

if TYPE_CHECKING:
    from contextlib import ExitStack
    from pathlib import Path

# Keep the buffer case for each file mode, matching the original nested
# image and image_file fixture cases.
IMAGE_CASES: tuple[
    tuple[Literal["high_quality_image", "image_file"], Literal["r+b", "rb"]],
    ...,
] = (
    ("high_quality_image", "r+b"),
    ("high_quality_image", "rb"),
    ("image_file", "r+b"),
    ("image_file", "rb"),
)


class ImageFactory:
    """Create image inputs whose file handles close with the fixture."""

    def __init__(
        self,
        *,
        high_quality_image: io.BytesIO,
        directory: Path,
        stack: ExitStack,
    ) -> None:
        """Keep the image bytes, temporary directory and cleanup stack."""
        self._high_quality_image = high_quality_image
        self._directory = directory
        self._stack = stack

    @beartype
    def create(
        self,
        *,
        source: Literal["high_quality_image", "image_file"],
        mode: Literal["r+b", "rb"],
    ) -> io.BytesIO | BinaryIO:
        """Open the file and return the selected image input."""
        file = self._directory / "image.jpg"
        _ = file.write_bytes(data=self._high_quality_image.getvalue())
        image_file = self._stack.enter_context(cm=file.open(mode=mode))
        if source == "high_quality_image":
            return self._high_quality_image
        return image_file
