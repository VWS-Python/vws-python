"""Async interface to the Vuforia VuMark Generation Web API."""

import json
from http import HTTPMethod, HTTPStatus
from typing import Self

from beartype import BeartypeConf, beartype

from vws._async_vws_request import async_target_api_request
from vws._vws_common import raise_for_vumark_result_code
from vws.exceptions.custom_exceptions import ServerError
from vws.exceptions.vws_exceptions import TooManyRequestsError
from vws.transports import AsyncHTTPXTransport, AsyncTransport
from vws.vumark_accept import VuMarkAccept


@beartype(conf=BeartypeConf(is_pep484_tower=True))
class AsyncVuMarkService:
    """An async interface to the Vuforia VuMark Generation Web
    API.
    """

    def __init__(
        self,
        *,
        server_access_key: str,
        server_secret_key: str,
        base_vws_url: str = "https://vws.vuforia.com",
        request_timeout_seconds: float | tuple[float, float] = 30.0,
        transport: AsyncTransport | None = None,
    ) -> None:
        """
        Args:
            server_access_key: A VWS server access key.
            server_secret_key: A VWS server secret key.
            base_vws_url: The base URL for the VWS API.
            request_timeout_seconds: The timeout for each
                HTTP request. This can be a float to set both
                the connect and read timeouts, or a
                (connect, read) tuple.
            transport: The async HTTP transport to use for
                requests. Defaults to
                ``AsyncHTTPXTransport()``.
        """
        self._server_access_key = server_access_key
        self._server_secret_key = server_secret_key
        self._base_vws_url = base_vws_url
        self._request_timeout_seconds = request_timeout_seconds
        self._transport = transport or AsyncHTTPXTransport()

    async def aclose(self) -> None:
        """Close the underlying transport if it supports closing."""
        close = getattr(self._transport, "aclose", None)
        if close is not None:
            await close()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *_args: object) -> None:
        """Exit the async context manager and close the transport."""
        await self.aclose()

    async def generate_vumark_instance(
        self,
        *,
        target_id: str,
        instance_id: str,
        accept: VuMarkAccept,
    ) -> bytes:
        """Generate a VuMark instance image.

        See
        https://developer.vuforia.com/library/vuforia-engine/web-api/vumark-generation-web-api/
        for parameter details.

        Args:
            target_id: The ID of the VuMark target.
            instance_id: The instance ID to encode in the
                VuMark.
            accept: The image format to return.

        Returns:
            The VuMark instance image bytes.

        Raises:
            ~vws.exceptions.vws_exceptions.AuthenticationFailureError: The
                secret key is not correct.
            ~vws.exceptions.vws_exceptions.FailError: There was an error with
                the request. For example, the given access key does not match a
                known database.
            ~vws.exceptions.vws_exceptions.InvalidAcceptHeaderError: The
                Accept header value is not supported.
            ~vws.exceptions.vws_exceptions.InvalidInstanceIdError: The
                instance ID is invalid. For example, it may be empty.
            ~vws.exceptions.vws_exceptions.InvalidTargetTypeError: The target
                is not a VuMark template target.
            ~vws.exceptions.vws_exceptions.RequestTimeTooSkewedError: There is
                an error with the time sent to Vuforia.
            ~vws.exceptions.vws_exceptions.TargetStatusNotSuccessError: The
                target is not in the success state.
            ~vws.exceptions.vws_exceptions.UnknownTargetError: The given target
                ID does not match a target in the database.
            ~vws.exceptions.custom_exceptions.ServerError: There is an error
                with Vuforia's servers.
            ~vws.exceptions.vws_exceptions.TooManyRequestsError: Vuforia is
                rate limiting access.
        """
        request_path = f"/targets/{target_id}/instances"
        content_type = "application/json"
        request_data = json.dumps(
            obj={"instance_id": instance_id},
        ).encode(encoding="utf-8")

        response = await async_target_api_request(
            content_type=content_type,
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method=HTTPMethod.POST,
            data=request_data,
            request_path=request_path,
            base_vws_url=self._base_vws_url,
            request_timeout_seconds=(self._request_timeout_seconds),
            extra_headers={"Accept": accept},
            transport=self._transport,
        )

        if (
            response.status_code == HTTPStatus.TOO_MANY_REQUESTS
        ):  # pragma: no cover
            # The Vuforia API returns a 429 response with no
            # JSON body.
            raise TooManyRequestsError(response=response)

        if (
            response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
        ):  # pragma: no cover
            raise ServerError(response=response)

        if response.status_code != HTTPStatus.OK:
            result_code = json.loads(s=response.text)["result_code"]
            raise_for_vumark_result_code(
                result_code=result_code,
                response=response,
            )
        return response.content
