import io

import pytest


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
