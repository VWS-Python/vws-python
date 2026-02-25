"""Tests for VWS exceptions raised from async clients."""

import io
import uuid
from http import HTTPStatus

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase
from mock_vws.states import States

from vws import AsyncVuMarkService, AsyncVWS
from vws.exceptions.custom_exceptions import (
    ServerError,
)
from vws.exceptions.vws_exceptions import (
    AuthenticationFailureError,
    BadImageError,
    FailError,
    ImageTooLargeError,
    InvalidInstanceIdError,
    MetadataTooLargeError,
    ProjectInactiveError,
    TargetNameExistError,
    TargetStatusProcessingError,
    UnknownTargetError,
)
from vws.vumark_accept import VuMarkAccept


@pytest.mark.asyncio
async def test_image_too_large(
    *,
    async_vws_client: AsyncVWS,
    png_too_large: io.BytesIO | io.BufferedRandom,
) -> None:
    """When giving an image which is too large, an
    ``ImageTooLarge`` exception is raised.
    """
    with pytest.raises(
        expected_exception=ImageTooLargeError,
    ) as exc:
        await async_vws_client.add_target(
            name="x",
            width=1,
            image=png_too_large,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_invalid_given_id(
    async_vws_client: AsyncVWS,
) -> None:
    """Giving an invalid ID causes an ``UnknownTarget``
    exception to be raised.
    """
    target_id = "12345abc"
    with pytest.raises(
        expected_exception=UnknownTargetError,
    ) as exc:
        await async_vws_client.delete_target(
            target_id=target_id,
        )
    assert exc.value.response.status_code == HTTPStatus.NOT_FOUND
    assert exc.value.target_id == target_id


@pytest.mark.asyncio
async def test_add_bad_name(
    *,
    async_vws_client: AsyncVWS,
    high_quality_image: io.BytesIO,
) -> None:
    """When a name with a bad character is given, a
    ``ServerError`` exception is raised.
    """
    max_char_value = 65535
    bad_name = chr(max_char_value + 1)
    with pytest.raises(
        expected_exception=ServerError,
    ) as exc:
        await async_vws_client.add_target(
            name=bad_name,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_fail(high_quality_image: io.BytesIO) -> None:
    """A ``Fail`` exception is raised when the server access key
    does not exist.
    """
    with MockVWS():
        async_vws_client = AsyncVWS(
            server_access_key=uuid.uuid4().hex,
            server_secret_key=uuid.uuid4().hex,
        )

        with pytest.raises(
            expected_exception=FailError,
        ) as exc:
            await async_vws_client.add_target(
                name="x",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_bad_image(
    async_vws_client: AsyncVWS,
) -> None:
    """A ``BadImage`` exception is raised when a non-image is
    given.
    """
    not_an_image = io.BytesIO(initial_bytes=b"Not an image")
    with pytest.raises(
        expected_exception=BadImageError,
    ) as exc:
        await async_vws_client.add_target(
            name="x",
            width=1,
            image=not_an_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_target_name_exist(
    *,
    async_vws_client: AsyncVWS,
    high_quality_image: io.BytesIO,
) -> None:
    """A ``TargetNameExist`` exception is raised after adding
    two targets with the same name.
    """
    await async_vws_client.add_target(
        name="x",
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )
    with pytest.raises(
        expected_exception=TargetNameExistError,
    ) as exc:
        await async_vws_client.add_target(
            name="x",
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN
    assert exc.value.target_name == "x"


@pytest.mark.asyncio
async def test_project_inactive(
    high_quality_image: io.BytesIO,
) -> None:
    """A ``ProjectInactive`` exception is raised if adding a
    target to an inactive database.
    """
    database = CloudDatabase(state=States.PROJECT_INACTIVE)
    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)
        async_vws_client = AsyncVWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        with pytest.raises(
            expected_exception=ProjectInactiveError,
        ) as exc:
            await async_vws_client.add_target(
                name="x",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_target_status_processing(
    *,
    async_vws_client: AsyncVWS,
    high_quality_image: io.BytesIO,
) -> None:
    """A ``TargetStatusProcessing`` exception is raised if
    trying to delete a target which is processing.
    """
    target_id = await async_vws_client.add_target(
        name="x",
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )

    with pytest.raises(
        expected_exception=TargetStatusProcessingError,
    ) as exc:
        await async_vws_client.delete_target(
            target_id=target_id,
        )

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN
    assert exc.value.target_id == target_id


@pytest.mark.asyncio
async def test_metadata_too_large(
    *,
    async_vws_client: AsyncVWS,
    high_quality_image: io.BytesIO,
) -> None:
    """A ``MetadataTooLarge`` exception is raised if the metadata
    given is too large.
    """
    with pytest.raises(
        expected_exception=MetadataTooLargeError,
    ) as exc:
        await async_vws_client.add_target(
            name="x",
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata="a" * 1024 * 1024 * 10,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_authentication_failure(
    high_quality_image: io.BytesIO,
) -> None:
    """An ``AuthenticationFailure`` exception is raised when the
    server secret key is incorrect.
    """
    database = CloudDatabase()

    async_vws_client = AsyncVWS(
        server_access_key=database.server_access_key,
        server_secret_key=uuid.uuid4().hex,
    )

    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)

        with pytest.raises(
            expected_exception=AuthenticationFailureError,
        ) as exc:
            await async_vws_client.add_target(
                name="x",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_invalid_instance_id(
    *,
    async_vumark_service_client: AsyncVuMarkService,
    vumark_target_id: str,
) -> None:
    """An ``InvalidInstanceId`` exception is raised when an
    empty instance ID is given.
    """
    with pytest.raises(
        expected_exception=InvalidInstanceIdError,
    ) as exc:
        await async_vumark_service_client.generate_vumark_instance(
            target_id=vumark_target_id,
            instance_id="",
            accept=VuMarkAccept.PNG,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
