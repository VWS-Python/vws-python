"""
Fixtures for images.
"""

import io

import pytest
from _pytest.fixtures import SubRequest

from tests.mock_vws.utils import make_image_file


@pytest.fixture
def image_file_success_state_low_rating() -> io.BytesIO:
    """
    Return an image file which is expected to have a 'success' status when
    added to a target and a low rating after processing.
    """
    return make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=5,
        height=5,
    )


@pytest.fixture
def png_rgb() -> io.BytesIO:
    """
    Return a 1x1 PNG file in the RGB color space.
    """
    return make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=1,
        height=1,
    )


@pytest.fixture
def corrupted_image_file() -> io.BytesIO:
    """
    Return an image file which is corrupted.
    """
    original_image = make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=1,
        height=1,
    )
    original_data = original_image.getvalue()
    corrupted_data = original_data.replace(b'IEND', b'\x00' + b'IEND')
    return io.BytesIO(corrupted_data)


@pytest.fixture
def image_file_failed_state() -> io.BytesIO:
    """
    Return an image file which is expected to be accepted by the add and
    update target endpoints, but get a "failed" status.

    This returns only one image, unlike ``image_files_failed_state`` in the
    interest of fast tests.
    """
    # This image gets a "failed" status because it is so small.
    return make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=1,
        height=1,
    )


@pytest.fixture(params=[('PNG', 'RGB'), ('JPEG', 'RGB'), ('PNG', 'L')])
def image_files_failed_state(request: SubRequest) -> io.BytesIO:
    """
    Return an image file which is expected to be accepted by the add and
    update target endpoints, but get a "failed" status.
    """
    # These images get a "failed" status because they are so small.
    file_format, color_space = request.param
    return make_image_file(
        file_format=file_format,
        color_space=color_space,
        width=1,
        height=1,
    )


@pytest.fixture(
    params=[('TIFF', 'RGB'), ('JPEG', 'CMYK')],
    ids=['Not accepted format', 'Not accepted color space'],
)
def bad_image_file(request: SubRequest) -> io.BytesIO:
    """
    Return an image file which is expected to cause a `BadImage` result when an
    attempt is made to add it to the target database.
    """
    file_format, color_space = request.param
    return make_image_file(
        file_format=file_format,
        color_space=color_space,
        width=1,
        height=1,
    )


@pytest.fixture()
def high_quality_image() -> io.BytesIO:
    """
    Return an image file which is expected to have a 'success' status when
    added to a target and a high tracking rating.

    At the time of writing, this image gains a tracking rating of 5.
    """
    path = 'tests/mock_vws/data/high_quality_image.jpg'
    with open(path, 'rb') as high_quality_image_file:
        return io.BytesIO(high_quality_image_file.read())


@pytest.fixture()
def different_high_quality_image() -> io.BytesIO:
    """
    Return an image file which is expected to have a 'success' status when
    added to a target and a high tracking rating.

    This is necessarily different to ``high_quality_image``.
    """
    path = 'tests/mock_vws/data/different_high_quality_image.jpg'
    with open(path, 'rb') as high_quality_image_file:
        return io.BytesIO(high_quality_image_file.read())
