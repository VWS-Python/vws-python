"""Tests for the async Model Target Web API client."""

import io
import uuid
import zipfile
from http import HTTPStatus

import pytest
from mock_vws import (
    MockVWS,
    ModelTargetFailureResponse,
    ModelTargetGenerationFailure,
    ModelTargetGenerationWarning,
)

from vws import AsyncModelTargetService
from vws.exceptions.custom_exceptions import ServerError
from vws.exceptions.model_target_exceptions import (
    ModelTargetAuthenticationError,
    ModelTargetDatasetNotDoneError,
    ModelTargetDatasetTimeoutError,
    ModelTargetError,
    ModelTargetOAuth2Error,
    ModelTargetValidationError,
    UnknownModelTargetDatasetError,
)
from vws.exceptions.vws_exceptions import TooManyRequestsError
from vws.model_target_datasets import (
    CadDataFormat,
    ModelTargetDatasetType,
    ModelTargetModel,
    RealisticAppearance,
)
from vws.reports import ModelTargetDatasetStatuses

# The mock accepts one hard-coded pair of Model Target Web API OAuth2
# credentials, which it does not expose.
_CLIENT_ID = "client-id"
_CLIENT_SECRET = "client-secret"  # noqa: S105

_DATASET_TYPES = [
    ModelTargetDatasetType.STANDARD,
    ModelTargetDatasetType.ADVANCED,
]


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
        client_id=_CLIENT_ID,
        client_secret=_CLIENT_SECRET,
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


class TestAccessToken:
    """Tests for getting an access token."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_token_is_a_bearer_token(
        *,
        async_model_target_client: AsyncModelTargetService,
    ) -> None:
        """An access token is given for valid credentials."""
        assert await async_model_target_client.get_access_token()

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("_mock_model_targets")
    async def test_invalid_credentials() -> None:
        """An exception is raised when the credentials are not known."""
        async with AsyncModelTargetService(
            client_id="not-a-client-id",
            client_secret="not-a-client-secret",  # noqa: S106
        ) as client:
            with pytest.raises(
                expected_exception=ModelTargetOAuth2Error,
            ) as exc:
                await client.get_access_token()

        assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED
        assert exc.value.error == "invalid_client"

    @staticmethod
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


class TestDatasetLifecycle:
    """Tests for the dataset lifecycle."""

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="dataset_type",
        argvalues=_DATASET_TYPES,
    )
    async def test_create_wait_download_delete(
        *,
        async_model_target_client: AsyncModelTargetService,
        model_target_model: ModelTargetModel,
        dataset_type: ModelTargetDatasetType,
    ) -> None:
        """A dataset can be created, downloaded and then deleted."""
        dataset_uuid = await async_model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=dataset_type,
        )

        report = await async_model_target_client.wait_for_dataset_generated(
            dataset_uuid=dataset_uuid,
            dataset_type=dataset_type,
        )

        assert report.status == ModelTargetDatasetStatuses.DONE
        assert report.dataset_uuid == dataset_uuid
        assert report.completed_at is not None
        assert report.eta is None
        assert report.error is None
        assert report.warning is None

        dataset = await async_model_target_client.download_dataset(
            dataset_uuid=dataset_uuid,
            dataset_type=dataset_type,
        )

        with zipfile.ZipFile(
            file=io.BytesIO(initial_bytes=dataset)
        ) as archive:
            assert archive.namelist() == ["MTDataset.dat", "MTDataset.xml"]

        await async_model_target_client.delete_dataset(
            dataset_uuid=dataset_uuid,
            dataset_type=dataset_type,
        )

        with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
            await async_model_target_client.get_dataset_status(
                dataset_uuid=dataset_uuid,
                dataset_type=dataset_type,
            )

    @staticmethod
    @pytest.mark.asyncio
    async def test_status_while_processing(
        *,
        async_model_target_client: AsyncModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A processing dataset has an estimated completion time."""
        dataset_uuid = await async_model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        report = await async_model_target_client.get_dataset_status(
            dataset_uuid=dataset_uuid,
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        assert report.status == ModelTargetDatasetStatuses.PROCESSING
        assert report.eta is not None
        assert report.completed_at is None

    @staticmethod
    @pytest.mark.asyncio
    async def test_download_while_processing(
        *,
        async_model_target_client: AsyncModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """A dataset cannot be downloaded before it is generated."""
        dataset_uuid = await async_model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        with pytest.raises(
            expected_exception=ModelTargetDatasetNotDoneError,
        ) as exc:
            await async_model_target_client.download_dataset(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert (
            exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        )
        assert exc.value.code == "UNSUPPORTED_STATE"

    @staticmethod
    @pytest.mark.asyncio
    async def test_dataset_is_visible_to_other_type(
        *,
        async_model_target_client: AsyncModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """Standard and advanced routes share datasets by UUID."""
        dataset_uuid = await async_model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model],
            dataset_type=ModelTargetDatasetType.ADVANCED,
        )

        report = await async_model_target_client.get_dataset_status(
            dataset_uuid=dataset_uuid,
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

        assert report.dataset_uuid == dataset_uuid

    @staticmethod
    @pytest.mark.asyncio
    async def test_advanced_dataset_takes_multiple_models(
        *,
        async_model_target_client: AsyncModelTargetService,
        model_target_model: ModelTargetModel,
    ) -> None:
        """An advanced dataset can be generated from multiple models."""
        other_model = ModelTargetModel(
            name="other-model",
            cad_data_blob="ZmFrZS1jYWQtZGF0YQ==",
            cad_data_format=CadDataFormat.GLB,
            realistic_appearance=RealisticAppearance.TRUE,
            views=[],
        )

        assert await async_model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model, other_model],
            dataset_type=ModelTargetDatasetType.ADVANCED,
        )


class TestUnknownDataset:
    """Tests for requests for datasets which do not exist."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_status(
        *,
        async_model_target_client: AsyncModelTargetService,
    ) -> None:
        """An exception is raised for an unknown dataset."""
        dataset_uuid = uuid.uuid4().hex
        with pytest.raises(
            expected_exception=UnknownModelTargetDatasetError,
        ) as exc:
            await async_model_target_client.get_dataset_status(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert exc.value.response.status_code == HTTPStatus.NOT_FOUND
        assert dataset_uuid in exc.value.message

    @staticmethod
    @pytest.mark.asyncio
    async def test_download(
        *,
        async_model_target_client: AsyncModelTargetService,
    ) -> None:
        """An exception is raised for an unknown dataset."""
        with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
            await async_model_target_client.download_dataset(
                dataset_uuid=uuid.uuid4().hex,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete(
        *,
        async_model_target_client: AsyncModelTargetService,
    ) -> None:
        """An exception is raised for an unknown dataset."""
        with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
            await async_model_target_client.delete_dataset(
                dataset_uuid=uuid.uuid4().hex,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )


class TestValidation:
    """Tests for requests which Vuforia rejects."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_no_cad_data(
        *,
        async_model_target_client: AsyncModelTargetService,
    ) -> None:
        """A model needs exactly one CAD data source."""
        with pytest.raises(
            expected_exception=ModelTargetValidationError,
        ) as exc:
            await async_model_target_client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[ModelTargetModel(name="model")],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

        assert exc.value.response.status_code == HTTPStatus.BAD_REQUEST
        (detail,) = exc.value.details
        assert detail.code == "VALIDATION_ERROR"


class TestGenerationResult:
    """Tests for datasets which Vuforia does not generate cleanly."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_generation_failure(
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
            async with AsyncModelTargetService(
                client_id=_CLIENT_ID,
                client_secret=_CLIENT_SECRET,
            ) as client:
                dataset_uuid = await client.create_dataset(
                    name="dataset",
                    target_sdk="11.0",
                    models=[model_target_model],
                    dataset_type=ModelTargetDatasetType.STANDARD,
                )

                report = await client.wait_for_dataset_generated(
                    dataset_uuid=dataset_uuid,
                    dataset_type=ModelTargetDatasetType.STANDARD,
                )

                assert report.status == ModelTargetDatasetStatuses.FAILED
                assert report.error is not None
                assert report.error.message == message

    @staticmethod
    @pytest.mark.asyncio
    async def test_generation_warning(
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
            async with AsyncModelTargetService(
                client_id=_CLIENT_ID,
                client_secret=_CLIENT_SECRET,
            ) as client:
                dataset_uuid = await client.create_dataset(
                    name="dataset",
                    target_sdk="11.0",
                    models=[model_target_model],
                    dataset_type=ModelTargetDatasetType.STANDARD,
                )

                report = await client.wait_for_dataset_generated(
                    dataset_uuid=dataset_uuid,
                    dataset_type=ModelTargetDatasetType.STANDARD,
                )

                assert report.status == ModelTargetDatasetStatuses.DONE
                assert report.warning is not None
                assert report.warning.target == dataset_uuid
                (detail,) = report.warning.details
                assert detail.code == "LOW_RECOGNITION_QUALITY"


class TestWaitForDatasetGenerated:
    """Tests for waiting for a dataset to be generated."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_timeout(*, model_target_model: ModelTargetModel) -> None:
        """An exception is raised when the wait times out."""
        with MockVWS(processing_time_seconds=60):
            async with AsyncModelTargetService(
                client_id=_CLIENT_ID,
                client_secret=_CLIENT_SECRET,
            ) as client:
                dataset_uuid = await client.create_dataset(
                    name="dataset",
                    target_sdk="11.0",
                    models=[model_target_model],
                    dataset_type=ModelTargetDatasetType.STANDARD,
                )

                with pytest.raises(
                    expected_exception=ModelTargetDatasetTimeoutError,
                ):
                    await client.wait_for_dataset_generated(
                        dataset_uuid=dataset_uuid,
                        dataset_type=ModelTargetDatasetType.STANDARD,
                        seconds_between_requests=0.01,
                        timeout_seconds=0.05,
                    )

                report = await client.get_dataset_status(
                    dataset_uuid=dataset_uuid,
                    dataset_type=ModelTargetDatasetType.STANDARD,
                )

        assert report.status == ModelTargetDatasetStatuses.PROCESSING
