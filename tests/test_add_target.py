import io

import pytest
from mock_vws import MockVWS, States
from requests import codes

from vws import VWS
from vws.exceptions import Fail, MetadataTooLarge, ProjectInactive, TargetNameExist, ImageTooLarge
from PIL import Image
import random
import base64


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


@pytest.fixture()
def client() -> VWS:
    with MockVWS() as mock:
        client = VWS(
            server_access_key=mock.server_access_key,
            server_secret_key=mock.server_secret_key,
        )

        yield client

class TestSuccess:
    def test_add_target(self, client: VWS, high_quality_image: io.BytesIO) -> None:
        client.add_target(name='x', width=1, image=high_quality_image)

    def test_add_two_targets(self, client: VWS, high_quality_image: io.BytesIO) -> None:
        client.add_target(name='x', width=1, image=high_quality_image)
        client.add_target(name='a', width=1, image=high_quality_image)

class TestName:
    def test_add_two_targets_same_name(self, client: VWS, high_quality_image: io.BytesIO) -> None:
        client.add_target(name='x', width=1, image=high_quality_image)

        with pytest.raises(TargetNameExist) as exc:
            client.add_target(name='x', width=1, image=high_quality_image)

class TestAuthentication:
    def test_authentication_error(self, high_quality_image: io.BytesIO) -> None:
        with MockVWS() as mock:
            client = VWS(
                server_access_key='a',
                server_secret_key=mock.server_secret_key,
            )

            with pytest.raises(Fail) as exc:
                target_id = client.add_target(
                    name='x',
                    width=1,
                    image=high_quality_image,
                )

            exception = exc.value
            assert exception.response.status_code == codes.BAD_REQUEST

class TestImage:
    def test_not_an_image(self):
        pass

    def test_image_too_large(self, client: VWS):
        max_bytes = 2.3 * 1024 * 1024
        width = height = 886

        width = width + 1
        height = height + 1
        png_too_large = make_image_file(
            file_format='PNG',
            color_space='RGB',
            width=width,
            height=height,
        )

        image_data = png_too_large.getvalue()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')
        image_content_size = len(image_data)
        # We check that the image we created is just slightly smaller than the
        # maximum file size.
        #
        # This is just because of the implementation details of
        # ``max_image_file``.
        assert image_content_size < max_bytes
        assert (image_content_size * 1.05) > max_bytes

        with pytest.raises(ImageTooLarge) as exc:
            client.add_target(name='x', width=1, image=png_too_large)


class TestApplicationMetadata:

    def test_none(self, client: VWS, high_quality_image: io.BytesIO):
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=None,
        )

    def test_given(self, client: VWS, high_quality_image: io.BytesIO):
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=b'a',
        )

    def test_too_large(self, client: VWS, high_quality_image: io.BytesIO):
        with pytest.raises(MetadataTooLarge):
            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                application_metadata=b'a' * 1024 * 1024,
            )

class TestInactiveProject:
    def test_inactive_project(self, high_quality_image: io.BytesIO):
        with MockVWS(real_http=False, state=States.PROJECT_INACTIVE) as mock:
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
