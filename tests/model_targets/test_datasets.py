"""Tests for Model Target datasets."""

import io
import json
import uuid
import zipfile
from http import HTTPStatus

import pytest
from mock_vws import (
    MockVWS,
    ModelTargetGenerationFailure,
    ModelTargetGenerationWarning,
)

from tests.model_targets.helpers import (
    CLIENT_CREDENTIALS,
    CLIENT_ID,
    response_with_status,
)
from vws import ModelTargetService
from vws._model_targets import access_token_from_response
from vws.exceptions.model_target_exceptions import (
    ModelTargetDatasetNotDoneError,
    ModelTargetDatasetTimeoutError,
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

_DATASET_TYPES = [
    ModelTargetDatasetType.STANDARD,
    ModelTargetDatasetType.ADVANCED,
]


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

    with zipfile.ZipFile(file=io.BytesIO(initial_bytes=dataset)) as archive:
        assert archive.namelist() == ["MTDataset.dat", "MTDataset.xml"]

    model_target_client.delete_dataset(
        dataset_uuid=dataset_uuid,
        dataset_type=dataset_type,
    )

    with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
        _ = model_target_client.get_dataset_status(
            dataset_uuid=dataset_uuid,
            dataset_type=dataset_type,
        )


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
        _ = model_target_client.download_dataset(
            dataset_uuid=dataset_uuid,
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert exc.value.code == "UNSUPPORTED_STATE"
    assert exc.value.target == dataset_uuid


def test_dataset_is_visible_to_other_type(
    *,
    model_target_client: ModelTargetService,
    model_target_model: ModelTargetModel,
) -> None:
    """Standard and advanced routes share datasets by UUID."""
    dataset_uuid = model_target_client.create_dataset(
        name="dataset",
        target_sdk="11.0",
        models=[model_target_model],
        dataset_type=ModelTargetDatasetType.STANDARD,
    )

    report = model_target_client.get_dataset_status(
        dataset_uuid=dataset_uuid,
        dataset_type=ModelTargetDatasetType.ADVANCED,
    )

    assert report.dataset_uuid == dataset_uuid


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
        views=[],
    )

    dataset_uuid = model_target_client.create_dataset(
        name="dataset",
        target_sdk="11.0",
        models=[model_target_model, other_model],
        dataset_type=ModelTargetDatasetType.ADVANCED,
    )

    assert bool(dataset_uuid)


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

    assert bool(
        model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )
    )


def test_get_status(*, model_target_client: ModelTargetService) -> None:
    """An exception is raised for an unknown dataset."""
    dataset_uuid = uuid.uuid4().hex
    with pytest.raises(
        expected_exception=UnknownModelTargetDatasetError,
    ) as exc:
        _ = model_target_client.get_dataset_status(
            dataset_uuid=dataset_uuid,
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

    assert exc.value.response.status_code == HTTPStatus.NOT_FOUND
    assert exc.value.code == "NOT_FOUND"
    assert dataset_uuid in exc.value.message


def test_download(*, model_target_client: ModelTargetService) -> None:
    """An exception is raised for an unknown dataset."""
    with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
        _ = model_target_client.download_dataset(
            dataset_uuid=uuid.uuid4().hex,
            dataset_type=ModelTargetDatasetType.STANDARD,
        )


def test_delete(*, model_target_client: ModelTargetService) -> None:
    """An exception is raised for an unknown dataset."""
    with pytest.raises(expected_exception=UnknownModelTargetDatasetError):
        model_target_client.delete_dataset(
            dataset_uuid=uuid.uuid4().hex,
            dataset_type=ModelTargetDatasetType.STANDARD,
        )


def test_no_cad_data(
    *,
    model_target_client: ModelTargetService,
) -> None:
    """A model needs exactly one CAD data source."""
    with pytest.raises(
        expected_exception=ModelTargetValidationError,
    ) as exc:
        _ = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[ModelTargetModel(name="model", views=[])],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

    assert exc.value.response.status_code == HTTPStatus.BAD_REQUEST
    assert exc.value.code == "BAD_REQUEST"
    (detail,) = exc.value.details
    assert detail.code == "VALIDATION_ERROR"
    assert "cadDataUrl" in detail.message


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
        _ = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )


def test_two_models_in_a_standard_dataset(
    *,
    model_target_client: ModelTargetService,
    model_target_model: ModelTargetModel,
) -> None:
    """A standard dataset takes exactly one model."""
    with pytest.raises(
        expected_exception=ModelTargetValidationError,
    ) as exc:
        _ = model_target_client.create_dataset(
            name="dataset",
            target_sdk="11.0",
            models=[model_target_model, model_target_model],
            dataset_type=ModelTargetDatasetType.STANDARD,
        )

    (detail,) = exc.value.details
    assert detail.message == "exactly one model should be provided"


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
            client_id=CLIENT_ID,
            client_secret=CLIENT_CREDENTIALS[1],
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
            _ = client.download_dataset(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )


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
            client_id=CLIENT_ID,
            client_secret=CLIENT_CREDENTIALS[1],
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

        assert bool(
            client.download_dataset(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )
        )


def test_timeout(*, model_target_model: ModelTargetModel) -> None:
    """An exception is raised when the wait times out."""
    with MockVWS(processing_time_seconds=60):
        client = ModelTargetService(
            client_id=CLIENT_ID,
            client_secret=CLIENT_CREDENTIALS[1],
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
            _ = client.wait_for_dataset_generated(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
                seconds_between_requests=0.01,
                timeout_seconds=0.05,
            )


@pytest.mark.parametrize(
    argnames="payload",
    argvalues=[
        {"access_token": 1, "expires_in": 3600},
        {"access_token": "token", "expires_in": []},
    ],
)
def test_invalid_oauth2_token_response_values(
    *, payload: dict[str, object]
) -> None:
    """OAuth token responses must contain correctly typed values."""
    response = response_with_status(
        text=json.dumps(obj=payload),
        status_code=HTTPStatus.OK,
    )

    with pytest.raises(expected_exception=ModelTargetOAuth2Error):
        _ = access_token_from_response(response=response)
