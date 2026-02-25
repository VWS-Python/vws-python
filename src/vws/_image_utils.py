"""Image utility functions shared across VWS modules."""

import io
from typing import BinaryIO

from beartype import beartype

ImageType = io.BytesIO | BinaryIO


@beartype
def get_image_data(image: ImageType) -> bytes:
    """Get the data of an image file."""
    original_tell = image.tell()
    image.seek(0)
    image_data = image.read()
    image.seek(original_tell)
    return image_data
