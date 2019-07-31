"""
Fixtures for images.
"""

import io
import random

import pytest
from PIL import Image


def _make_image_file(
    file_format: str,
    color_space: str,
    width: int,
    height: int,
) -> io.BytesIO:
    """
    Return an image file in the given format and color space.

    The image file is filled with randomly colored pixels.

    Args:
        file_format: See
            http://pillow.readthedocs.io/en/3.1.x/handbook/image-file-formats.html
        color_space: One of "L", "RGB", or "CMYK".
        width: The width, in pixels of the image.
        height: The width, in pixels of the image.

    Returns:
        An image file in the given format and color space.
    """
    image_buffer = io.BytesIO()
    reds = random.choices(population=range(0, 255), k=width * height)
    greens = random.choices(population=range(0, 255), k=width * height)
    blues = random.choices(population=range(0, 255), k=width * height)
    pixels = list(zip(reds, greens, blues))
    image = Image.new(color_space, (width, height))
    image.putdata(pixels)
    image.save(image_buffer, file_format)
    image_buffer.seek(0)
    return image_buffer


@pytest.fixture()
def high_quality_image() -> io.BytesIO:
    """
    Return an image file which is expected to have a 'success' status when
    added to a target and a high tracking rating.

    At the time of writing, this image gains a tracking rating of 5.
    """
    path = 'tests/data/high_quality_image.jpg'
    with open(path, 'rb') as high_quality_image_file:
        return io.BytesIO(high_quality_image_file.read())


@pytest.fixture
def image_file_failed_state() -> io.BytesIO:
    """
    Return an image file which is expected to be accepted by the add and
    update target endpoints, but get a "failed" status.
    """
    # This image gets a "failed" status because it is so small.
    return _make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=1,
        height=1,
    )


@pytest.fixture
def png_too_large() -> io.BytesIO:
    """
    Return a PNG file which has dimensions which are too large to be added to
    a Vuforia database.
    """
    width = height = 890

    return _make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=width,
        height=height,
    )
