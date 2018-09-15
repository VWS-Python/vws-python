"""
Tests for helper function for adding a target to a Vuforia database.
"""

import io
import random

import pytest
from mock_vws import MockVWS, States
from PIL import Image
from requests import codes

from mock_vws import MockVWS

from vws import VWS
from vws.exceptions import (
    BadImage,
    Fail,
    ImageTooLarge,
    MetadataTooLarge,
    ProjectInactive,
    TargetNameExist,
)


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
        color_space: One of "L", "RGB", or "CMYK". "L" means greyscale.
        width: The width, in pixels of the image.
        height: The width, in pixels of the image.

    Returns:
        An image file in the given format and color space.
    """
    image_buffer = io.BytesIO()
    image = Image.new(color_space, (width, height))
    pixels = image.load()
    for i in range(height):
        for j in range(width):
            red = random.randint(0, 255)
            green = random.randint(0, 255)
            blue = random.randint(0, 255)
            if color_space != 'L':
                pixels[j, i] = (red, green, blue)
    image.save(image_buffer, file_format)
    image_buffer.seek(0)
    return image_buffer


class TestSuccess:
    """
    Tests for successfully adding a target.
    """

    def test_add_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        client.add_target(name='x', width=1, image=high_quality_image)

    def test_add_two_targets(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding two targets with different names.
        """
        client.add_target(name='x', width=1, image=high_quality_image)
        client.add_target(name='a', width=1, image=high_quality_image)


<<<<<<< HEAD
class TestName:
    """
    Tests for the ``name`` parameter to ``add_target``.
    """

    def test_add_two_targets_same_name(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        A ``TargetNameExist`` exception is raised after adding two targets with
        the same name.
        """
        client.add_target(name='x', width=1, image=high_quality_image)

        with pytest.raises(TargetNameExist):
            client.add_target(name='x', width=1, image=high_quality_image)


class TestAuthentication:
    """
    Tests for authentication issues.
    """

    def test_authentication_error(
        self,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        A ``Fail`` exception is raised when there are authentication issues.
        """
        with MockVWS() as mock:
            client = VWS(
                server_access_key='a',
                server_secret_key=mock.server_secret_key,
            )

            with pytest.raises(Fail) as exc:
                client.add_target(
                    name='x',
                    width=1,
                    image=high_quality_image,
                )

            exception = exc.value
            assert exception.response.status_code == codes.BAD_REQUEST


class TestImage:
    """
    Tests for the ``image`` parameter to ``add_target``.
    """

    def test_not_an_image(self, client: VWS) -> None:
        """
        A ``BadImage`` exception is raised when a non-image is given.
        """
        not_an_image = io.BytesIO(b'Not an image')
        with pytest.raises(BadImage):
            client.add_target(name='x', width=1, image=not_an_image)

    def test_image_too_large(self, client: VWS) -> None:
        """
        An ``ImageTooLarge`` exception is raised when the given image is too
        large.
        """
        width = height = 890

        png_too_large = make_image_file(
            file_format='PNG',
            color_space='RGB',
            width=width,
            height=height,
        )

        with pytest.raises(ImageTooLarge):
            client.add_target(name='x', width=1, image=png_too_large)


class TestApplicationMetadata:
    """
    Tests for the ``application_metadata`` parameter to ``add_target``.
    """

    def test_none(self, client: VWS, high_quality_image: io.BytesIO) -> None:
        """
        No exception is raised when ``None`` is given.
        """
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=None,
        )

    def test_given(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when bytes are given.
        """
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=b'a',
        )

    def test_too_large(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        A ``MetadataTooLarge`` exception is raised if the metadata given is too
        large.
        """
        with pytest.raises(MetadataTooLarge):
            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                application_metadata=b'a' * 1024 * 1024,
            )


class TestCustomBaseURL:
    """
    Tests for adding images to databases under custom VWS URLs.
    """

    def test_custom_base_url(self, high_quality_image: io.BytesIO) -> None:
        """
        It is possible to use add a target to a database under a custom VWS
        URL.
        """
        base_vws_url = 'http://example.com'
        with MockVWS(base_vws_url=base_vws_url) as mock:
            client = VWS(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
                base_vws_url=base_vws_url,
            )

            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )


class TestInactiveProject:
    """
    Tests for using an inactive project.
    """

    def test_inactive_project(self, high_quality_image: io.BytesIO) -> None:
        """
        A ``ProjectInactive`` exception is raised if adding a target to an
        inactive database.
        """
        with MockVWS(state=States.PROJECT_INACTIVE) as mock:
            client = VWS(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
            )

            with pytest.raises(ProjectInactive):
                client.add_target(
                    name='x',
                    width=1,
                    image=high_quality_image,
                )
