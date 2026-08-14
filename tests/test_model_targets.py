"""Tests for the Model Target Web API client."""

import io
import json
import uuid
import zipfile
from http import HTTPStatus

import pytest
from beartype import beartype
from freezegun import freeze_time
from mock_vws import (
    MockVWS,
    ModelTargetGenerationFailure,
    ModelTargetGenerationWarning,
)

from vws import ModelTargetService
from vws.exceptions.model_target_exceptions import (
    ModelTargetAuthenticationError,
    ModelTargetDatasetNotDoneError,
    ModelTargetDatasetTimeoutError,
    ModelTargetError,
    ModelTargetOAuth2Error,
    ModelTargetValidationError,
    UnknownModelTargetDatasetError,
)
from vws.model_target_datasets import (
    CadDataFormat,
    GuideViewPosition,
    ModelTargetDatasetType,
    ModelTargetModel,
    ModelTargetView,
    RealisticAppearance,
)
from vws.reports import ModelTargetDatasetStatuses
from vws.response import Response
from vws.transports import RequestsTransport, Transport

# The mock accepts one hard-coded pair of Model Target Web API OAuth2
# credentials, which it does not expose.
_CLIENT_ID = "client-id"
_CLIENT_SECRET = "client-secret"  # noqa: S105

_DATASET_TYPES = [
    ModelTargetDatasetType.STANDARD,
    ModelTargetDatasetType.ADVANCED,
]


@beartype
def _response(*, text: str) -> Response:
    """Get a response with a given body.

    Args:
        text: The body of the response.

    Returns:
        A response with the given body.
    """
    content = text.encode(encoding="utf-8")
    return Response(
        text=text,
        url="https://vws.vuforia.com/modeltargets/datasets",
        status_code=HTTPStatus.BAD_REQUEST,
        headers={},
        request_body=None,
        tell_position=len(content),
        content=content,
    )


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


@beartype
class _BadTokenTransport:
    """A transport which replaces each bearer token with an invalid
    one.
    """

    def __init__(self, *, transport: Transport) -> None:
        """
        Args:
            transport: The transport to make requests with.
        """
        self._transport = transport

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
        """Make a request with an invalid bearer token.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            request_timeout: The request timeout.

        Returns:
            A Response populated from the HTTP response.
        """
        given_headers = dict(headers)
        authorization = given_headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            given_headers["Authorization"] = "Bearer not-a-json-web-token"

        return self._transport(
            method=method,
            url=url,
            headers=given_headers,
            data=data,
            request_timeout=request_timeout,
        )


class TestAccessToken:
    """Tests for getting an access token."""

    @staticmethod
    @pytest.mark.usefixtures("_mock_model_targets")
    def test_token_is_a_bearer_token() -> None:
        """An access token is given for valid credentials."""
        client = ModelTargetService(
            client_id=_CLIENT_ID,
            client_secret=_CLIENT_SECRET,
        )

        assert client.get_access_token()

    @staticmethod
    @pytest.mark.usefixtures("_mock_model_targets")
    def test_token_is_reused(
        *,
        model_target_model: ModelTargetModel,
    ) -> None:
        """One access token is used for multiple requests."""
        transport = _CountingTransport(transport=RequestsTransport())
        client = ModelTargetService(
            client_id=_CLIENT_ID,
            client_secret=_CLIENT_SECRET,
            transport=transport,
        )

        for _ in range(2):
            client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        token_urls = [url for url in transport.urls if "oauth2" in url]
        assert len(token_urls) == 1
        transport.close()

    @staticmethod
    @pytest.mark.usefixtures("_mock_model_targets")
    def test_expired_token_is_replaced(
        *,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A new access token is requested once the old one expires."""
        transport = _CountingTransport(transport=RequestsTransport())
        client = ModelTargetService(
            client_id=_CLIENT_ID,
            client_secret=_CLIENT_SECRET,
            transport=transport,
        )

        with freeze_time(time_to_freeze="2026-01-01") as frozen_time:
            client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )
            # Mock tokens last an hour.
            frozen_time.tick(delta=60 * 60 + 1)
            client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        token_urls = [url for url in transport.urls if "oauth2" in url]
        expected_token_request_count = 2
        assert len(token_urls) == expected_token_request_count

    @staticmethod
    @pytest.mark.usefixtures("_mock_model_targets")
    def test_invalid_credentials() -> None:
        """An exception is raised when the credentials are not known."""
        client = ModelTargetService(
            client_id="not-a-client-id",
            client_secret="not-a-client-secret",  # noqa: S106
        )

        with pytest.raises(
            expected_exception=ModelTargetOAuth2Error,
        ) as exc:
            client.get_access_token()

        assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED
        assert exc.value.error == "invalid_client"
        assert not exc.value.error_description

    @staticmethod
    @pytest.mark.usefixtures("_mock_model_targets")
    def test_invalid_bearer_token(
        *,
        model_target_model: ModelTargetModel,
    ) -> None:
        """An exception is raised when the bearer token is not
        accepted.
        """
        transport = _BadTokenTransport(transport=RequestsTransport())
        client = ModelTargetService(
            client_id=_CLIENT_ID,
            client_secret=_CLIENT_SECRET,
            transport=transport,
        )

        with pytest.raises(
            expected_exception=ModelTargetAuthenticationError,
        ) as exc:
            client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED
        assert exc.value.target == "jwt"
        assert exc.value.message
        transport.close()


class TestDatasetLifecycle:
    """Tests for the dataset lifecycle."""

    @staticmethod
    @pytest.mark.parametrize(
        argnames="dataset_type",
        argvalues=_DATASET_TYPES,
    )
    def test_create_wait_download_delete(
        *,
        model_target_client: ModelTargetService,
        model_target_model: ModelTargetModel,
        dataset_type: ModelTargetDatasetType,
    ) -> None:
        """A dataset can be created, downloaded and then deleted."""
        dataset_uuid = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=dataset_type,
        )

        report = model_target_client.wait_for_dataset_generated(
            dataset_uuid=dataset_uuid,
            dataset_type=dataset_type,
        )

        assert report.status == ModelTargetDatasetStatuses.DONE
        assert report.dataset_uuid == dataset_uuid
        assert report.completed_at is not None
        assert report.completed_at >= report.created_at
        assert report.eta is None
        assert report.error is None
        assert report.warning is None

        dataset = model_target_client.download_dataset(
            dataset_uuid=dataset_uuid,
            dataset_type=dataset_type,
        )

        with zipfile.ZipFile(
            file=io.BytesIO(initial_bytes=dataset)
        ) as archive:
            dataset_json = json.loads(s=archive.read(name="dataset.json"))

        assert dataset_json["uuid"] == dataset_uuid
        assert dataset_json["type"] == dataset_type.value

        model_target_client.delete_dataset(
            dataset_uuid=dataset_uuid,
            dataset_type=dataset_type,
        )

        with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
            model_target_client.get_dataset_status(
                dataset_uuid=dataset_uuid,
                dataset_type=dataset_type,
            )

    @staticmethod
    def test_status_while_processing(
        *,
        model_target_client: ModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A processing dataset has an estimated completion time."""
        dataset_uuid = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        report = model_target_client.get_dataset_status(
            dataset_uuid=dataset_uuid,
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        assert report.status == ModelTargetDatasetStatuses.PROCESSING
        assert report.eta is not None
        assert report.eta >= report.created_at
        assert report.completed_at is None

    @staticmethod
    def test_download_while_processing(
        *,
        model_target_client: ModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A dataset cannot be downloaded before it is generated."""
        dataset_uuid = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        with pytest.raises(
            expected_exception=ModelTargetDatasetNotDoneError,
        ) as exc:
            model_target_client.download_dataset(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert (
            exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        )
        assert exc.value.code == "UNSUPPORTED_STATE"
        assert exc.value.target == dataset_uuid

    @staticmethod
    def test_dataset_types_are_separate(
        *,
        model_target_client: ModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A dataset is not visible to requests for the other type."""
        dataset_uuid = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
            model_target_client.get_dataset_status(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.ADVANCED,
            )

    @staticmethod
    def test_advanced_dataset_takes_multiple_models(
        *,
        model_target_client: ModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """An advanced dataset can be generated from multiple models."""
        other_model = ModelTargetModel(
            name="other-model",
            cad_data_blob="ZmFrZS1jYWQtZGF0YQ==",
            cad_data_format=CadDataFormat.GLB,
            realistic_appearance=RealisticAppearance.TRUE,
        )

        dataset_uuid = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model, other_model],
            dataset_type=ModelTargetDatasetType.ADVANCED,
        )

        assert dataset_uuid

    @staticmethod
    def test_state_based_model(
        *,
        model_target_client: ModelTargetService,
    ) -> None:
        """A State-Based Model Target dataset can be created."""
        configuration = json.dumps(obj={"states": {"open": {}, "closed": {}}})
        model = ModelTargetModel(
            name="model",
            cad_data_url="https://example.com/model.zip",
            cad_data_format=CadDataFormat.ZIP,
            state_based_configuration_json_string=configuration,
            views=[
                ModelTargetView(
                    name="front",
                    guide_view_position=GuideViewPosition(
                        rotation=[0.0, 0.0, 0.0, 1.0],
                        translation=[0.0, 0.0, 1.0],
                    ),
                    states=["open"],
                ),
            ],
        )

        assert model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )


class TestUnknownDataset:
    """Tests for requests for datasets which do not exist."""

    @staticmethod
    def test_get_status(*, model_target_client: ModelTargetService) -> None:
        """An exception is raised for an unknown dataset."""
        dataset_uuid = uuid.uuid4().hex
        with pytest.raises(
            expected_exception=UnknownModelTargetDatasetError,
        ) as exc:
            model_target_client.get_dataset_status(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert exc.value.response.status_code == HTTPStatus.NOT_FOUND
        assert exc.value.code == "NOT_FOUND"
        assert dataset_uuid in exc.value.message

    @staticmethod
    def test_download(*, model_target_client: ModelTargetService) -> None:
        """An exception is raised for an unknown dataset."""
        with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
            model_target_client.download_dataset(
                dataset_uuid=uuid.uuid4().hex,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

    @staticmethod
    def test_delete(*, model_target_client: ModelTargetService) -> None:
        """An exception is raised for an unknown dataset."""
        with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
            model_target_client.delete_dataset(
                dataset_uuid=uuid.uuid4().hex,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )


class TestValidation:
    """Tests for requests which Vuforia rejects."""

    @staticmethod
    def test_no_cad_data(
        *,
        model_target_client: ModelTargetService,
    ) -> None:
        """A model needs exactly one CAD data source."""
        with pytest.raises(
            expected_exception=ModelTargetValidationError,
        ) as exc:
            model_target_client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[ModelTargetModel(name="model")],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert exc.value.response.status_code == HTTPStatus.BAD_REQUEST
        assert exc.value.code == "BAD_REQUEST"
        (detail,) = exc.value.details
        assert detail.code == "VALIDATION_ERROR"
        assert "cadDataUrl" in detail.message

    @staticmethod
    def test_two_cad_data_sources(
        *,
        model_target_client: ModelTargetService,
    ) -> None:
        """A model cannot give two CAD data sources."""
        model = ModelTargetModel(
            name="model",
            cad_data_url="https://example.com/model.zip",
            cad_data_blob="ZmFrZS1jYWQtZGF0YQ==",
        )

        with pytest.raises(expected_exception=ModelTargetValidationError):
            model_target_client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

    @staticmethod
    def test_two_models_in_a_standard_dataset(
        *,
        model_target_client: ModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A standard dataset takes exactly one model."""
        with pytest.raises(
            expected_exception=ModelTargetValidationError,
        ) as exc:
            model_target_client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model, model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        (detail,) = exc.value.details
        assert detail.message == "exactly one model should be provided"


class TestGenerationResult:
    """Tests for datasets which Vuforia does not generate cleanly."""

    @staticmethod
    def test_generation_failure(
        *,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A dataset which fails to generate reports the failure."""
        message = "Model Target dataset generation failed"
        failure = ModelTargetGenerationFailure(message=message)
        with MockVWS(
            processing_time_seconds=0.2,
            model_target_generation_failure=failure,
        ):
            client = ModelTargetService(
                client_id=_CLIENT_ID,
                client_secret=_CLIENT_SECRET,
            )
            dataset_uuid = client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

            report = client.wait_for_dataset_generated(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

            assert report.status == ModelTargetDatasetStatuses.FAILED
            assert report.error is not None
            assert report.error.message == message
            assert report.warning is None

            with pytest.raises(
                expected_exception=ModelTargetDatasetNotDoneError,
            ):
                client.download_dataset(
                    dataset_uuid=dataset_uuid,
                    dataset_type=ModelTargetDatasetType.STANDARD,
                )

    @staticmethod
    def test_generation_warning(
        *,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A dataset which generates with a warning reports the
        warning.
        """
        warning = ModelTargetGenerationWarning()
        with MockVWS(
            processing_time_seconds=0.2,
            model_target_generation_warning=warning,
        ):
            client = ModelTargetService(
                client_id=_CLIENT_ID,
                client_secret=_CLIENT_SECRET,
            )
            dataset_uuid = client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

            report = client.wait_for_dataset_generated(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

            assert report.status == ModelTargetDatasetStatuses.DONE
            assert report.error is None
            assert report.warning is not None
            assert report.warning.message == warning.message
            assert report.warning.target == dataset_uuid
            (detail,) = report.warning.details
            assert detail.code == "LOW_RECOGNITION_QUALITY"

            assert client.download_dataset(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )


class TestWaitForDatasetGenerated:
    """Tests for waiting for a dataset to be generated."""

    @staticmethod
    def test_timeout(*, model_target_model: ModelTargetModel) -> None:
        """An exception is raised when the wait times out."""
        with MockVWS(processing_time_seconds=60):
            client = ModelTargetService(
                client_id=_CLIENT_ID,
                client_secret=_CLIENT_SECRET,
            )
            dataset_uuid = client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

            with pytest.raises(
                expected_exception=ModelTargetDatasetTimeoutError,
            ):
                client.wait_for_dataset_generated(
                    dataset_uuid=dataset_uuid,
                    dataset_type=ModelTargetDatasetType.STANDARD,
                    seconds_between_requests=0.01,
                    timeout_seconds=0.05,
                )


class TestErrorEnvelope:
    """Tests for reading responses which are not shaped like Model Target
    Web API errors.
    """

    @staticmethod
    @pytest.mark.parametrize(
        argnames="text",
        argvalues=[
            "",
            "Not JSON",
            "[]",
            "{}",
            '{"error": "not-an-object"}',
            '{"transaction_id": "abc", "result_code": "Fail"}',
        ],
    )
    def test_unknown_error_shape(*, text: str) -> None:
        """An error without a Model Target error object gives empty
        values.
        """
        error = ModelTargetError(response=_response(text=text))

        assert not error.code
        assert not error.message
        assert not error.target
        assert not error.details

    @staticmethod
    def test_error_without_details() -> None:
        """An error which gives no details has no details."""
        text = json.dumps(obj={"error": {"code": "ERROR", "message": "No"}})
        error = ModelTargetError(response=_response(text=text))

        assert error.code == "ERROR"
        assert error.message == "No"
        assert not error.target
        assert not error.details

    @staticmethod
    @pytest.mark.parametrize(
        argnames="text",
        argvalues=["Not JSON", "[]", "{}"],
    )
    def test_unknown_oauth2_error_shape(*, text: str) -> None:
        """An OAuth2 error without an error code gives empty values."""
        error = ModelTargetOAuth2Error(response=_response(text=text))

        assert not error.error
        assert not error.error_description

    @staticmethod
    def test_oauth2_error_description() -> None:
        """An OAuth2 error description is given when Vuforia gives one."""
        description = "Missing or invalid authorization header"
        text = json.dumps(
            obj={
                "error": "invalid_request",
                "error_description": description,
            },
        )
        error = ModelTargetOAuth2Error(response=_response(text=text))

        assert error.error == "invalid_request"
        assert error.error_description == description


class TestBaseVWSURL:
    """Tests for using a custom base URL."""

    @staticmethod
    def test_custom_base_url(
        *,
        model_target_model: ModelTargetModel,
    ) -> None:
        """The Model Target Web API can be served from a URL with a
        path.
        """
        base_vws_url = "https://example.com/vws"
        with MockVWS(
            base_vws_url=base_vws_url,
            processing_time_seconds=0.2,
        ):
            client = ModelTargetService(
                client_id=_CLIENT_ID,
                client_secret=_CLIENT_SECRET,
                base_vws_url=base_vws_url,
            )
            dataset_uuid = client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

            report = client.get_dataset_status(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert report.dataset_uuid == dataset_uuid
