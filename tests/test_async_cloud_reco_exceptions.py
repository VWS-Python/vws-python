"""Tests for exceptions raised when using the
AsyncCloudRecoService.
"""

import io
import uuid
from http import HTTPStatus

import pytest
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase
from mock_vws.states import States

from vws import AsyncCloudRecoService
from vws.exceptions.cloud_reco_exceptions import (
    AuthenticationFailureError,
    InactiveProjectError,
    MaxNumResultsOutOfRangeError,
)
from vws.exceptions.custom_exceptions import (
    RequestEntityTooLargeError,
)


@pytest.mark.asyncio
async def test_too_many_max_results(
    *,
    async_cloud_reco_client: AsyncCloudRecoService,
    high_quality_image: io.BytesIO,
) -> None:
    """A ``MaxNumResultsOutOfRange`` error is raised if the given
    ``max_num_results`` is out of range.
    """
    with pytest.raises(
        expected_exception=MaxNumResultsOutOfRangeError,
    ) as exc:
        await async_cloud_reco_client.query(
            image=high_quality_image,
            max_num_results=51,
        )

    expected_value = (
        "Integer out of range (51) in form data part "
        "'max_result'. "
        "Accepted range is from 1 to 50 (inclusive)."
    )
    assert str(object=exc.value) == exc.value.response.text == expected_value


@pytest.mark.asyncio
async def test_image_too_large(
    *,
    async_cloud_reco_client: AsyncCloudRecoService,
    png_too_large: io.BytesIO | io.BufferedRandom,
) -> None:
    """A ``RequestEntityTooLarge`` exception is raised if an
    image which is too large is given.
    """
    with pytest.raises(
        expected_exception=RequestEntityTooLargeError,
    ) as exc:
        await async_cloud_reco_client.query(
            image=png_too_large,
        )

    assert (
        exc.value.response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    )


@pytest.mark.asyncio
async def test_authentication_failure(
    high_quality_image: io.BytesIO,
) -> None:
    """An ``AuthenticationFailure`` exception is raised when the
    client secret key is incorrect.
    """
    database = CloudDatabase()
    async_cloud_reco_client = AsyncCloudRecoService(
        client_access_key=database.client_access_key,
        client_secret_key=uuid.uuid4().hex,
    )
    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)

        with pytest.raises(
            expected_exception=AuthenticationFailureError,
        ) as exc:
            await async_cloud_reco_client.query(
                image=high_quality_image,
            )

        assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_inactive_project(
    high_quality_image: io.BytesIO,
) -> None:
    """An ``InactiveProject`` exception is raised when querying
    an inactive database.
    """
    database = CloudDatabase(state=States.PROJECT_INACTIVE)
    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)
        async_cloud_reco_client = AsyncCloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
        )

        with pytest.raises(
            expected_exception=InactiveProjectError,
        ) as exc:
            await async_cloud_reco_client.query(
                image=high_quality_image,
            )

        response = exc.value.response
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.tell_position != 0
