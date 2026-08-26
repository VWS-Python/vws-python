"""Internal helpers for the Vuforia Model Target Web API."""

import base64
import json
from collections.abc import Sequence  # noqa: TC003
from http import HTTPStatus
from typing import Any

from beartype import BeartypeConf, beartype

from vws.exceptions.custom_exceptions import ServerError
from vws.exceptions.model_target_exceptions import (
    ModelTargetAuthenticationError,
    ModelTargetDatasetNotDoneError,
    ModelTargetError,
    ModelTargetOAuth2Error,
    ModelTargetValidationError,
    UnknownModelTargetDatasetError,
)
from vws.exceptions.vws_exceptions import TooManyRequestsError
from vws.model_target_datasets import (  # noqa: TC001
    ModelTargetDatasetType,
    ModelTargetModel,
    ModelTargetView,
)
from vws.reports import ModelTargetDatasetStatusReport
from vws.response import Response  # noqa: TC001

OAUTH2_TOKEN_PATH = "/oauth2/token"  # noqa: S105
OAUTH2_TOKEN_BODY = b"grant_type=client_credentials"
OAUTH2_TOKEN_CONTENT_TYPE = "application/x-www-form-urlencoded"  # noqa: S105
JSON_CONTENT_TYPE = "application/json"

_DATASET_COLLECTION_PATHS = {
    "standard": "/modeltargets/datasets",
    "advanced": "/modeltargets/advancedDatasets",
}
_EXCEPTIONS_BY_STATUS_CODE: dict[int, type[ModelTargetError]] = {
    HTTPStatus.BAD_REQUEST: ModelTargetValidationError,
    HTTPStatus.UNAUTHORIZED: ModelTargetAuthenticationError,
    HTTPStatus.NOT_FOUND: UnknownModelTargetDatasetError,
    HTTPStatus.UNPROCESSABLE_ENTITY: ModelTargetDatasetNotDoneError,
}


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def oauth2_token_headers(
    *, client_id: str, client_secret: str
) -> dict[str, str]:
    """Get the headers for a request for an access token.

    Args:
        client_id: A Model Target Web API client ID.
        client_secret: A Model Target Web API client secret.

    Returns:
        The headers to send with a token request.
    """
    credentials = f"{client_id}:{client_secret}".encode()
    encoded_credentials = base64.b64encode(s=credentials).decode(
        encoding="ascii",
    )
    return {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": OAUTH2_TOKEN_CONTENT_TYPE,
    }


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def access_token_from_response(*, response: Response) -> tuple[str, float]:
    """Get an access token and its lifetime from a token response.

    Args:
        response: The response from Vuforia's token endpoint.

    Returns:
        The access token, and the number of seconds until it expires.

    Raises:
        ~vws.exceptions.model_target_exceptions.ModelTargetOAuth2Error:
            Vuforia did not give an access token.
    """
    if response.status_code != HTTPStatus.OK:
        raise ModelTargetOAuth2Error(response=response)

    response_data = dict(json.loads(s=response.text))
    return response_data["access_token"], float(response_data["expires_in"])


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def dataset_collection_path(*, dataset_type: ModelTargetDatasetType) -> str:
    """Get the path of the endpoint for datasets of a given type.

    Args:
        dataset_type: The kind of dataset to get the path for.

    Returns:
        The path of the dataset collection endpoint.
    """
    return _DATASET_COLLECTION_PATHS[dataset_type.value]


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def dataset_path(
    *,
    dataset_type: ModelTargetDatasetType,
    dataset_uuid: str,
) -> str:
    """Get the path of the endpoint for one dataset.

    Args:
        dataset_type: The kind of dataset to get the path for.
        dataset_uuid: The UUID of the dataset.

    Returns:
        The path of the dataset endpoint.
    """
    collection_path = dataset_collection_path(dataset_type=dataset_type)
    return f"{collection_path}/{dataset_uuid}"


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def dataset_status_path(
    *,
    dataset_type: ModelTargetDatasetType,
    dataset_uuid: str,
) -> str:
    """Get the path of the status endpoint for one dataset.

    Args:
        dataset_type: The kind of dataset to get the path for.
        dataset_uuid: The UUID of the dataset.

    Returns:
        The path of the dataset status endpoint.
    """
    return (
        dataset_path(dataset_type=dataset_type, dataset_uuid=dataset_uuid)
        + "/status"
    )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def dataset_download_path(
    *,
    dataset_type: ModelTargetDatasetType,
    dataset_uuid: str,
) -> str:
    """Get the path of the download endpoint for one dataset.

    Args:
        dataset_type: The kind of dataset to get the path for.
        dataset_uuid: The UUID of the dataset.

    Returns:
        The path of the dataset download endpoint.
    """
    return (
        dataset_path(dataset_type=dataset_type, dataset_uuid=dataset_uuid)
        + "/dataset"
    )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def _view_dict(*, view: ModelTargetView) -> dict[str, Any]:
    """Get the request representation of a guide view.

    Args:
        view: The guide view to represent.

    Returns:
        The guide view, as it is sent to Vuforia.
    """
    view_dict: dict[str, Any] = {
        "name": view.name,
        "guideViewPosition": {
            "rotation": list(view.guide_view_position.rotation),
            "translation": list(view.guide_view_position.translation),
        },
    }
    if view.states is not None:
        view_dict["states"] = list(view.states)

    return view_dict


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def _model_dict(*, model: ModelTargetModel) -> dict[str, Any]:
    """Get the request representation of a model.

    Args:
        model: The model to represent.

    Returns:
        The model, as it is sent to Vuforia.
    """
    model_dict: dict[str, Any] = {"name": model.name}
    optional_values: dict[str, str | None] = {
        "automaticColoring": model.automatic_coloring,
        "cadDataBlob": model.cad_data_blob,
        "cadDataFormat": model.cad_data_format,
        "cadDataUrl": model.cad_data_url,
        "motionHint": model.motion_hint,
        "optimizeTrackingFor": model.optimize_tracking_for,
        "realisticAppearance": model.realistic_appearance,
        "simplify": model.simplify,
        "stateBasedConfigurationJsonString": (
            model.state_based_configuration_json_string
        ),
        "trackingMode": model.tracking_mode,
    }
    for field_name, value in optional_values.items():
        if value is not None:
            model_dict[field_name] = str(object=value)

    if model.views is not None:
        model_dict["views"] = [_view_dict(view=view) for view in model.views]

    return model_dict


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def dataset_request_body(
    *,
    name: str,
    target_sdk: str,
    models: Sequence[ModelTargetModel],
) -> bytes:
    """Get the request body for creating a Model Target dataset.

    Args:
        name: The name of the dataset.
        target_sdk: The Vuforia Engine version to generate the dataset
            for.
        models: The models to generate the dataset from.

    Returns:
        The body of the request.
    """
    request_dict = {
        "models": [_model_dict(model=model) for model in models],
        "name": name,
        "targetSdk": target_sdk,
    }
    return json.dumps(obj=request_dict).encode(encoding="utf-8")


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def raise_for_error(*, response: Response) -> None:
    """Raise an exception for an unsuccessful Model Target Web API
    response.

    Args:
        response: A response from the Model Target Web API.

    Raises:
        ~vws.exceptions.model_target_exceptions.ModelTargetAuthenticationError:
            The request was not authenticated.
        ~vws.exceptions.model_target_exceptions.ModelTargetValidationError:
            Vuforia rejected the dataset creation request.
        ~vws.exceptions.model_target_exceptions.UnknownModelTargetDatasetError:
            No dataset of the given type matches the given UUID.
        ~vws.exceptions.model_target_exceptions.ModelTargetDatasetNotDoneError:
            The dataset has not been generated.
        ~vws.exceptions.model_target_exceptions.ModelTargetError: Vuforia
            returned another error.
        ~vws.exceptions.custom_exceptions.ServerError: There is an error
            with Vuforia's servers.
        ~vws.exceptions.vws_exceptions.TooManyRequestsError: Vuforia is
            rate limiting access.
    """
    if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        # The Vuforia API returns a 429 response with no JSON body.
        raise TooManyRequestsError(response=response)

    if response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise ServerError(response=response)

    if response.status_code < HTTPStatus.BAD_REQUEST:
        return

    exception_type = _EXCEPTIONS_BY_STATUS_CODE.get(
        response.status_code,
        ModelTargetError,
    )
    raise exception_type(response=response)


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def dataset_uuid_from_response(*, response: Response) -> str:
    """Get the UUID of a created dataset.

    Args:
        response: A response to a dataset creation request.

    Returns:
        The UUID of the created dataset.
    """
    response_data = dict(json.loads(s=response.text))
    return str(object=response_data["uuid"])


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def status_report_from_response(
    *,
    response: Response,
) -> ModelTargetDatasetStatusReport:
    """Get a dataset status report from a status response.

    Args:
        response: A response to a dataset status request.

    Returns:
        The status of the dataset.
    """
    response_data = dict(json.loads(s=response.text))
    return ModelTargetDatasetStatusReport.from_response_dict(
        response_dict=response_data,
    )
