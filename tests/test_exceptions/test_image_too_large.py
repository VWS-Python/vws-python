"""
Tests for giving an image which is too large.
"""

import io
import random

import pytest
from PIL import Image
from requests import codes

from vws import VWS
from vws.exceptions import ImageTooLarge


def make_image_file(
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


def test_image_too_large(client: VWS) -> None:
    """
    When giving an image which is too large, an ``ImageTooLarge`` exception is
    raised.
    """
    width = height = 890

    png_too_large = make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=width,
        height=height,
    )

    with pytest.raises(ImageTooLarge) as exc:
        client.add_target(name='x', width=1, image=png_too_large)

    assert exc.value.response.status_code == codes.UNPROCESSABLE_ENTITY
