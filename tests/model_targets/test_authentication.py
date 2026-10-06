"""Tests for Model Target authentication."""

import secrets
from http import HTTPStatus

import pytest
from beartype import beartype
from freezegun import freeze_time
from mock_vws import (
    MockVWS,
    ModelTargetFailureResponse,
)

from tests.model_targets.helpers import CLIENT_CREDENTIALS, CLIENT_ID
from vws import ModelTargetService
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

# beartype resolves the decorated transport's return type at runtime.
from vws.response import Response  # noqa: TC001
from vws.transports import RequestsTransport, Transport


@beartype
class _CountingTransport:
    """A transport which counts the requests made to each path."""

    def __init__(self, *, transport: Transport) -> None:
        """
        Args:
            transport: The transport to make requests with.
        """
        self._transport = transport
        self.urls: list[str] = []

    def close(self) -> None:
        """Close the wrapped transport."""
        self._transport.close()

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Make a request, recording the URL.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            request_timeout: The request timeout.

        Returns:
            A Response populated from the HTTP response.
        """
        self.urls.append(url)
        return self._transport(
            method=method,
            url=url,
            headers=headers,
            data=data,
            request_timeout=request_timeout,
        )


@pytest.mark.usefixtures("_mock_model_targets")
def test_token_is_a_bearer_token() -> None:
    """An access token is given for valid credentials."""
    client = ModelTargetService(
        client_id=CLIENT_ID,
        client_secret=CLIENT_CREDENTIALS[1],
    )

    assert bool(client.get_access_token())


@pytest.mark.usefixtures("_mock_model_targets")
def test_token_is_reused(
    *,
    model_target_model: ModelTargetModel,
) -> None:
    """One access token is used for multiple requests."""
    transport = _CountingTransport(transport=RequestsTransport())
    client = ModelTargetService(
        client_id=CLIENT_ID,
        client_secret=CLIENT_CREDENTIALS[1],
        transport=transport,
    )

    for _ in range(2):
        _ = client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

    token_urls = [url for url in transport.urls if "oauth2" in url]
    assert len(token_urls) == 1
    transport.close()


@pytest.mark.usefixtures("_mock_model_targets")
def test_expired_token_is_replaced(
    *,
    model_target_model: ModelTargetModel,
) -> None:
    """A new access token is requested once the old one expires."""
    transport = _CountingTransport(transport=RequestsTransport())
    client = ModelTargetService(
        client_id=CLIENT_ID,
        client_secret=CLIENT_CREDENTIALS[1],
        transport=transport,
    )

    with freeze_time(time_to_freeze="2026-01-01") as frozen_time:
        _ = client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )
        # Mock tokens last an hour.
        _ = frozen_time.tick(delta=60 * 60 + 1)
        _ = client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

    token_urls = [url for url in transport.urls if "oauth2" in url]
    expected_token_request_count = 2
    assert len(token_urls) == expected_token_request_count


@pytest.mark.usefixtures("_mock_model_targets")
def test_invalid_credentials() -> None:
    """An exception is raised when the credentials are not known."""
    client = ModelTargetService(
        client_id="not-a-client-id",
        client_secret=secrets.token_hex(),
    )

    with pytest.raises(
        expected_exception=ModelTargetOAuth2Error,
    ) as exc:
        _ = client.get_access_token()

    assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.value.error == "invalid_client"
    assert not bool(exc.value.error_description)


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
def test_dataset_error_response(
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
    client = ModelTargetService(
        client_id=CLIENT_ID,
        client_secret=CLIENT_CREDENTIALS[1],
    )

    with (
        MockVWS(model_target_failure_response=failure),
        pytest.raises(expected_exception=expected_exception) as exc,
    ):
        _ = client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

    assert isinstance(exc.value, expected_exception)
    assert exc.value.response.status_code == status_code
    assert exc.value.response.text == body
