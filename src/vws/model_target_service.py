"""Interface to the Vuforia Model Target Web API."""

import time
from collections.abc import Sequence  # noqa: TC003
from http import HTTPMethod

from beartype import BeartypeConf, beartype

from vws._model_targets import (
    JSON_CONTENT_TYPE,
    OAUTH2_TOKEN_BODY,
    OAUTH2_TOKEN_PATH,
    access_token_from_response,
    dataset_collection_path,
    dataset_download_path,
    dataset_path,
    dataset_request_body,
    dataset_status_path,
    dataset_uuid_from_response,
    oauth2_token_headers,
    raise_for_error,
    status_report_from_response,
)
from vws.exceptions.model_target_exceptions import (
    ModelTargetDatasetTimeoutError,
)
from vws.model_target_datasets import (  # noqa: TC001
    ModelTargetDatasetType,
    ModelTargetModel,
)
from vws.reports import (
    ModelTargetDatasetStatuses,
    ModelTargetDatasetStatusReport,
)
from vws.response import Response  # noqa: TC001
from vws.transports import RequestsTransport, Transport

_TOKEN_EXPIRY_MARGIN_SECONDS = 60.0


@beartype(conf=BeartypeConf(is_pep484_tower=True))
class ModelTargetService:
    """An interface to the Vuforia Model Target Web API."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        base_vws_url: str = "https://vws.vuforia.com",
        request_timeout_seconds: float | tuple[float, float] = 30.0,
        transport: Transport | None = None,
    ) -> None:
        """
        Args:
            client_id: A Model Target Web API OAuth2 client
                ID.
            client_secret: A Model Target Web API OAuth2
                client secret.
            base_vws_url: The base URL for the VWS API, which
                also serves the Model Target Web API.
            request_timeout_seconds: The timeout for each
                HTTP request. This can be a float to set both
                the connect and read timeouts, or a
                (connect, read) tuple.
            transport: The HTTP transport to use for
                requests. Defaults to
                ``RequestsTransport()``.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_vws_url = base_vws_url
        self._request_timeout_seconds = request_timeout_seconds
        self._transport = (
            transport if transport is not None else RequestsTransport()
        )
        self._access_token: str | None = None
        self._access_token_expiry_time = 0.0

    def get_access_token(self) -> str:
        """Get an OAuth2 access token for the Model Target Web API.

        A token is requested only when the client has no token which is
        still valid, so this can be called before each request.

        Returns:
            A bearer token.

        Raises:
            ~vws.exceptions.model_target_exceptions.ModelTargetOAuth2Error:
                Vuforia did not give an access token. For example, the
                given client ID and client secret may not match a set of
                Model Target Web API credentials.
        """
        request_time = time.monotonic()
        if (
            self._access_token is not None
            and request_time < self._access_token_expiry_time
        ):
            return self._access_token

        response = self._transport(
            method=HTTPMethod.POST,
            url=self._base_vws_url.rstrip("/") + OAUTH2_TOKEN_PATH,
            headers=oauth2_token_headers(
                client_id=self._client_id,
                client_secret=self._client_secret,
            ),
            data=OAUTH2_TOKEN_BODY,
            request_timeout=self._request_timeout_seconds,
        )

        access_token, expires_in_seconds = access_token_from_response(
            response=response,
        )
        self._access_token = access_token
        self._access_token_expiry_time = (
            request_time + expires_in_seconds - _TOKEN_EXPIRY_MARGIN_SECONDS
        )
        return access_token

    def make_request(
        self,
        *,
        method: str,
        data: bytes,
        request_path: str,
        extra_headers: dict[str, str] | None = None,
    ) -> Response:
        """Make an authenticated request to the Model Target Web API.

        Args:
            method: The HTTP method which will be used in
                the request.
            data: The request body which will be used in the
                request.
            request_path: The path to the endpoint which
                will be used in the request.
            extra_headers: Additional headers to include in
                the request.

        Returns:
            The response to the request.

        Raises:
            ~vws.exceptions.model_target_exceptions.ModelTargetError:
                Vuforia returned an error.
            ~vws.exceptions.custom_exceptions.ServerError:
                There is an error with Vuforia's servers.
            ~vws.exceptions.vws_exceptions.TooManyRequestsError:
                Vuforia is rate limiting access.
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            **(extra_headers or {}),
        }

        response = self._transport(
            method=method,
            url=self._base_vws_url.rstrip("/") + request_path,
            headers=headers,
            data=data,
            request_timeout=self._request_timeout_seconds,
        )

        raise_for_error(response=response)
        return response

    def create_dataset(
        self,
        *,
        name: str,
        target_sdk: str,
        models: Sequence[ModelTargetModel],
        dataset_type: ModelTargetDatasetType,
    ) -> str:
        """Start generating a Model Target dataset.

        Vuforia generates the dataset in the background, so it is not
        available to download immediately. Use
        :meth:`wait_for_dataset_generated` to wait for it.

        Args:
            name: The name of the dataset.
            target_sdk: The Vuforia Engine version to generate the dataset
                for.
            models: The models to generate the dataset from. A standard
                dataset takes exactly one model.
            dataset_type: Whether to create a standard or an advanced
                dataset.

        Returns:
            The UUID of the new dataset.

        Raises:
            ~vws.exceptions.model_target_exceptions.ModelTargetAuthenticationError:
                The request was not authenticated.
            ~vws.exceptions.model_target_exceptions.ModelTargetValidationError:
                Vuforia rejected the request. For example, a model may
                give neither a CAD data URL nor a CAD data blob.
            ~vws.exceptions.model_target_exceptions.ModelTargetOAuth2Error:
                Vuforia did not give an access token.
        """
        response = self.make_request(
            method=HTTPMethod.POST,
            data=dataset_request_body(
                name=name,
                target_sdk=target_sdk,
                models=models,
            ),
            request_path=dataset_collection_path(dataset_type=dataset_type),
            extra_headers={"Content-Type": JSON_CONTENT_TYPE},
        )

        return dataset_uuid_from_response(response=response)

    def get_dataset_status(
        self,
        *,
        dataset_uuid: str,
        dataset_type: ModelTargetDatasetType,
    ) -> ModelTargetDatasetStatusReport:
        """Get the status of a Model Target dataset.

        Args:
            dataset_uuid: The UUID of the dataset, as given by
                :meth:`create_dataset`.
            dataset_type: The kind of dataset to get the status of.

        Returns:
            The status of the dataset.

        Raises:
            ~vws.exceptions.model_target_exceptions.ModelTargetAuthenticationError:
                The request was not authenticated.
            ~vws.exceptions.model_target_exceptions.UnknownModelTargetDatasetError:
                No dataset of the given type matches the given UUID.
            ~vws.exceptions.model_target_exceptions.ModelTargetOAuth2Error:
                Vuforia did not give an access token.
        """
        response = self.make_request(
            method=HTTPMethod.GET,
            data=b"",
            request_path=dataset_status_path(
                dataset_type=dataset_type,
                dataset_uuid=dataset_uuid,
            ),
        )

        return status_report_from_response(response=response)

    def wait_for_dataset_generated(
        self,
        *,
        dataset_uuid: str,
        dataset_type: ModelTargetDatasetType,
        seconds_between_requests: float = 0.2,
        timeout_seconds: float = 60 * 5,
    ) -> ModelTargetDatasetStatusReport:
        """Wait for Vuforia to finish generating a Model Target dataset.

        A dataset which failed to generate is also finished, so the
        returned report may have a
        :attr:`~.ModelTargetDatasetStatusReport.status` of
        ``FAILED``.

        Args:
            dataset_uuid: The UUID of the dataset, as given by
                :meth:`create_dataset`.
            dataset_type: The kind of dataset to wait for.
            seconds_between_requests: The number of seconds to wait between
                requests made while polling the dataset's status.
            timeout_seconds: The maximum number of seconds to wait for the
                dataset to be generated.

        Returns:
            The status of the dataset once it is no longer processing.

        Raises:
            ~vws.exceptions.model_target_exceptions.ModelTargetDatasetTimeoutError:
                The dataset was not generated within ``timeout_seconds``
                seconds.
            ~vws.exceptions.model_target_exceptions.UnknownModelTargetDatasetError:
                No dataset of the given type matches the given UUID.
        """
        start_time = time.monotonic()
        while True:
            report = self.get_dataset_status(
                dataset_uuid=dataset_uuid,
                dataset_type=dataset_type,
            )
            if report.status != ModelTargetDatasetStatuses.PROCESSING:
                return report

            elapsed_time = time.monotonic() - start_time
            if elapsed_time > timeout_seconds:
                raise ModelTargetDatasetTimeoutError

            time.sleep(seconds_between_requests)

    def download_dataset(
        self,
        *,
        dataset_uuid: str,
        dataset_type: ModelTargetDatasetType,
    ) -> bytes:
        """Download a generated Model Target dataset.

        Args:
            dataset_uuid: The UUID of the dataset, as given by
                :meth:`create_dataset`.
            dataset_type: The kind of dataset to download.

        Returns:
            The dataset, as the bytes of a zip file.

        Raises:
            ~vws.exceptions.model_target_exceptions.ModelTargetAuthenticationError:
                The request was not authenticated.
            ~vws.exceptions.model_target_exceptions.UnknownModelTargetDatasetError:
                No dataset of the given type matches the given UUID.
            ~vws.exceptions.model_target_exceptions.ModelTargetDatasetNotDoneError:
                Vuforia has not generated the dataset.
            ~vws.exceptions.model_target_exceptions.ModelTargetOAuth2Error:
                Vuforia did not give an access token.
        """
        response = self.make_request(
            method=HTTPMethod.GET,
            data=b"",
            request_path=dataset_download_path(
                dataset_type=dataset_type,
                dataset_uuid=dataset_uuid,
            ),
        )

        return response.content

    def delete_dataset(
        self,
        *,
        dataset_uuid: str,
        dataset_type: ModelTargetDatasetType,
    ) -> None:
        """Delete a Model Target dataset.

        Args:
            dataset_uuid: The UUID of the dataset, as given by
                :meth:`create_dataset`.
            dataset_type: The kind of dataset to delete.

        Raises:
            ~vws.exceptions.model_target_exceptions.ModelTargetAuthenticationError:
                The request was not authenticated.
            ~vws.exceptions.model_target_exceptions.UnknownModelTargetDatasetError:
                No dataset of the given type matches the given UUID.
            ~vws.exceptions.model_target_exceptions.ModelTargetOAuth2Error:
                Vuforia did not give an access token.
        """
        self.make_request(
            method=HTTPMethod.DELETE,
            data=b"",
            request_path=dataset_path(
                dataset_type=dataset_type,
                dataset_uuid=dataset_uuid,
            ),
        )
