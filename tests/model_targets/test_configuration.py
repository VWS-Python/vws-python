"""Tests for Model Target configuration."""

from mock_vws import (
    MockVWS,
)

from tests.model_target_credentials import CLIENT_CREDENTIALS, CLIENT_ID
from vws import ModelTargetService
from vws.model_target_datasets import (
    ModelTargetDatasetType,
    ModelTargetModel,
)


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
            client_id=CLIENT_ID,
            client_secret=CLIENT_CREDENTIALS[1],
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
