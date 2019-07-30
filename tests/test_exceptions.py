"""
Tests for various exceptions.
"""

import io
import random

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from mock_vws.states import States
from PIL import Image
from requests import codes

from vws import VWS, CloudRecoService
from vws.exceptions import (
    AuthenticationFailure,
    BadImage,
    Fail,
    ImageTooLarge,
    MetadataTooLarge,
    ProjectInactive,
    TargetNameExist,
    TargetStatusNotSuccess,
    TargetStatusProcessing,
    UnknownTarget,
)


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


def test_image_too_large(vws_client: VWS) -> None:
    """
    When giving an image which is too large, an ``ImageTooLarge`` exception is
    raised.
    """
    width = height = 890

    png_too_large = _make_image_file(
        file_format='PNG',
        color_space='RGB',
        width=width,
        height=height,
    )

    with pytest.raises(ImageTooLarge) as exc:
        vws_client.add_target(name='x', width=1, image=png_too_large)

    assert exc.value.response.status_code == codes.UNPROCESSABLE_ENTITY


def test_invalid_given_id(vws_client: VWS) -> None:
    """
    Giving an invalid ID to a helper which requires a target ID to be given
    causes an ``UnknownTarget`` exception to be raised.
    """
    with pytest.raises(UnknownTarget) as exc:
        vws_client.delete_target(target_id='x')
    assert exc.value.response.status_code == codes.NOT_FOUND


def test_request_quota_reached() -> None:
    """
    See https://github.com/adamtheturtle/vws-python/issues/822 for writing
    this test.
    """


def test_fail(high_quality_image: io.BytesIO) -> None:
    """
    A ``Fail`` exception is raised when the server access key does not exist.
    """
    with MockVWS():
        vws_client = VWS(
            server_access_key='a',
            server_secret_key='a',
        )

        with pytest.raises(Fail) as exc:
            vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )

        assert exc.value.response.status_code == codes.BAD_REQUEST


def test_bad_image(vws_client: VWS) -> None:
    """
    A ``BadImage`` exception is raised when a non-image is given.
    """
    not_an_image = io.BytesIO(b'Not an image')
    with pytest.raises(BadImage) as exc:
        vws_client.add_target(name='x', width=1, image=not_an_image)

    assert exc.value.response.status_code == codes.UNPROCESSABLE_ENTITY


def test_target_name_exist(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetNameExist`` exception is raised after adding two targets with
    the same name.
    """
    vws_client.add_target(name='x', width=1, image=high_quality_image)
    with pytest.raises(TargetNameExist) as exc:
        vws_client.add_target(name='x', width=1, image=high_quality_image)

    assert exc.value.response.status_code == codes.FORBIDDEN


def test_project_inactive(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``ProjectInactive`` exception is raised if adding a target to an
    inactive database.
    """
    database = VuforiaDatabase(state=States.PROJECT_INACTIVE)
    with MockVWS() as mock:
        mock.add_database(database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        with pytest.raises(ProjectInactive) as exc:
            vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )

    assert exc.value.response.status_code == codes.FORBIDDEN


def test_target_status_processing(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetStatusProcessing`` exception is raised if trying to delete a
    target which is processing.
    """
    target_id = vws_client.add_target(
        name='x',
        width=1,
        image=high_quality_image,
    )

    with pytest.raises(TargetStatusProcessing) as exc:
        vws_client.delete_target(target_id=target_id)

    assert exc.value.response.status_code == codes.FORBIDDEN


def test_metadata_too_large(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``MetadataTooLarge`` exception is raised if the metadata given is too
    large.
    """
    with pytest.raises(MetadataTooLarge) as exc:
        vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=b'a' * 1024 * 1024,
        )

    assert exc.value.response.status_code == codes.UNPROCESSABLE_ENTITY


def test_authentication_failure(high_quality_image: io.BytesIO) -> None:
    """
    An ``AuthenticationFailure`` exception is raised when the server access key
    exists but the server secret key is incorrect, or when a client key is
    incorrect.
    """
    database = VuforiaDatabase()
    with MockVWS() as mock:
        mock.add_database(database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key='a',
        )

        with pytest.raises(AuthenticationFailure) as exc:
            vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )

        assert exc.value.response.status_code == codes.UNAUTHORIZED

        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key='a',
        )

        with pytest.raises(AuthenticationFailure) as exc:
            cloud_reco_client.query(image=high_quality_image)

        assert exc.value.response.status_code == codes.UNAUTHORIZED


def test_target_status_not_success(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetStatusNotSuccess`` exception is raised when updating a target
    which has a status which is not "Success".
    """
    target_id = vws_client.add_target(
        name='x',
        width=1,
        image=high_quality_image,
    )

    with pytest.raises(TargetStatusNotSuccess) as exc:
        vws_client.update_target(target_id=target_id)

    assert exc.value.response.status_code == codes.FORBIDDEN
