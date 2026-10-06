"""Tests for asynchronous Model Target authentication."""

import secrets
from http import HTTPStatus

import pytest
from mock_vws import (
    MockVWS,
    ModelTargetFailureResponse,
)

from tests.async_model_targets.helpers import CLIENT_CREDENTIALS, CLIENT_ID
from vws import AsyncModelTargetService
from vws.exceptions.custom_exceptions import ServerError
from vws.exceptions.model_target_exceptions import (
    ModelTargetAuthenticationError,
    ModelTargetError,
    ModelTargetOAuth2Error,
)
from vws.exceptions.vws_exceptions import TooManyRequestsError
from vws.model_target_datasets import (
    ModelTargetDatasetType,
    ModelTargetModel,
)


async def _assert_dataset_error_response(
    *,
    model_target_model: ModelTargetModel,
    status_code: HTTPStatus,
    body: str,
    expected_exception: (
        type[ModelTargetError | TooManyRequestsError | ServerError]
    ),
) -> None:
    """Assert that a mocked dataset failure maps to an exception."""
    async with AsyncModelTargetService(
        client_id=CLIENT_ID,
        client_secret=CLIENT_CREDENTIALS[1],
    ) as client:
        with pytest.raises(
            expected_exception=(
                ModelTargetError,
                TooManyRequestsError,
                ServerError,
            )
        ) as exc:
            await client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

    assert isinstance(exc.value, expected_exception)
    assert exc.value.response.status_code == status_code
    assert exc.value.response.text == body


@pytest.mark.asyncio
async def test_token_is_a_bearer_token(
    *,
    async_model_target_client: AsyncModelTargetService,
) -> None:
    """An access token is given for valid credentials."""
    assert bool(await async_model_target_client.get_access_token())


@pytest.mark.asyncio
@pytest.mark.usefixtures("_mock_model_targets")
async def test_invalid_credentials() -> None:
    """An exception is raised when the credentials are not known."""
    async with AsyncModelTargetService(
        client_id="not-a-client-id",
        client_secret=secrets.token_hex(),
    ) as client:
        with pytest.raises(
            expected_exception=ModelTargetOAuth2Error,
        ) as exc:
            await client.get_access_token()

    assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.value.error == "invalid_client"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("status_code", "body", "expected_exception"),
    argvalues=[
        pytest.param(
            HTTPStatus.UNAUTHORIZED,
            '{"error":{"code":"AUTHENTICATION_ERROR","message":"No"}}',
            ModelTargetAuthenticationError,
            id="authentication",
        ),
        pytest.param(
            HTTPStatus.FORBIDDEN,
            '{"error":{"code":"FORBIDDEN","message":"Denied"}}',
            ModelTargetError,
            id="generic-json",
        ),
        pytest.param(
            HTTPStatus.CONFLICT,
            "not json",
            ModelTargetError,
            id="generic-non-json",
        ),
        pytest.param(
            HTTPStatus.TOO_MANY_REQUESTS,
            "rate limited",
            TooManyRequestsError,
            id="rate-limit",
        ),
        pytest.param(
            HTTPStatus.BAD_GATEWAY,
            "server error",
            ServerError,
            id="server-error",
        ),
    ],
)
async def test_dataset_error_response(
    *,
    model_target_model: ModelTargetModel,
    status_code: HTTPStatus,
    body: str,
    expected_exception: (
        type[ModelTargetError | TooManyRequestsError | ServerError]
    ),
) -> None:
    """Dataset failures map to exceptions through the mock."""
    failure = ModelTargetFailureResponse(
        status_code=status_code,
        body=body,
    )

    with MockVWS(model_target_failure_response=failure):
        await _assert_dataset_error_response(
            model_target_model=model_target_model,
            status_code=status_code,
            body=body,
            expected_exception=expected_exception,
        )
