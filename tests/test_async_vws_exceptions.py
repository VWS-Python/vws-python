"""Tests for VWS exceptions raised from async clients."""

from __future__ import annotations

import uuid
from http import HTTPStatus

import pytest
from mock_vws import MockVWS, VuMarkGenerationFailure

from vws import AsyncVuMarkService
from vws.exceptions.vws_exceptions import (
    AuthorizationFailedError,
    InvalidInstanceIdError,
    LicenseCheckFailedError,
    QuotaExceededError,
)
from vws.vumark_accept import VuMarkAccept


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("failure", "exception_type", "status_code"),
    argvalues=[
        (
            VuMarkGenerationFailure.QUOTA_EXCEEDED,
            QuotaExceededError,
            HTTPStatus.FORBIDDEN,
        ),
        (
            VuMarkGenerationFailure.LICENSE_CHECK_FAILED,
            LicenseCheckFailedError,
            HTTPStatus.FORBIDDEN,
        ),
        (
            VuMarkGenerationFailure.AUTHORIZATION_FAILED,
            AuthorizationFailedError,
            HTTPStatus.UNAUTHORIZED,
        ),
    ],
)
async def test_documented_vumark_error_codes(
    *,
    failure: VuMarkGenerationFailure,
    exception_type: type[
        QuotaExceededError | LicenseCheckFailedError | AuthorizationFailedError
    ],
    status_code: HTTPStatus,
) -> None:
    """Documented VuMark failures raise matching exceptions."""
    with MockVWS(vumark_generation_failure=failure):
        vumark_service = AsyncVuMarkService(
            server_access_key=uuid.uuid4().hex,
            server_secret_key=uuid.uuid4().hex,
        )
        with pytest.raises(expected_exception=exception_type) as exc:
            await vumark_service.generate_vumark_instance(
                target_id="exampletargetid",
                instance_id="example_instance_id",
                accept=VuMarkAccept.PNG,
            )
        await vumark_service.aclose()

    assert exc.value.response.status_code == status_code
    assert failure.value in exc.value.response.text
