"""Tests for `httpx` transports."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
import pytest
import respx

from vws import (
    VWS,
    AsyncCloudRecoService,
    AsyncVuMarkService,
    AsyncVWS,
    CloudRecoService,
    VuMarkService,
)
from vws.exceptions.custom_exceptions import ServerError
from vws.exceptions.vws_exceptions import TooManyRequestsError
from vws.response import Response
from vws.transports import (
    AsyncHTTPXTransport,
    HTTPXTransport,
)
from vws.vumark_accept import VuMarkAccept

if TYPE_CHECKING:
    import io


class _FalsyTransport:
    """A sync transport that is falsy but protocol-conforming."""

    def __bool__(self) -> bool:
        """Return ``False`` so truthiness checks would skip this
        transport.
        """
        return False

    def close(self) -> None:
        """Close the transport."""

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Return a successful API response for the requested URL."""
        del method, headers, request_timeout
        if url.endswith("/query"):
            body = '{"result_code":"Success","results":[]}'
            return Response(
                text=body,
                url=url,
                status_code=HTTPStatus.OK,
                headers={},
                request_body=data,
                tell_position=0,
                content=body.encode(),
            )
        if "/instances" in url:
            content = b"vumark-bytes"
            return Response(
                text="",
                url=url,
                status_code=HTTPStatus.OK,
                headers={},
                request_body=data,
                tell_position=0,
                content=content,
            )
        body = '{"result_code":"Success","results":[]}'
        return Response(
            text=body,
            url=url,
            status_code=HTTPStatus.OK,
            headers={},
            request_body=data,
            tell_position=0,
            content=body.encode(),
        )


class _FalsyAsyncTransport:
    """An async transport that is falsy but protocol-conforming."""

    def __bool__(self) -> bool:
        """Return ``False`` so truthiness checks would skip this
        transport.
        """
        return False

    async def aclose(self) -> None:
        """Close the transport."""

    async def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Return a successful API response for the requested URL."""
        del method, headers, request_timeout
        if url.endswith("/query"):
            body = '{"result_code":"Success","results":[]}'
            return Response(
                text=body,
                url=url,
                status_code=HTTPStatus.OK,
                headers={},
                request_body=data,
                tell_position=0,
                content=body.encode(),
            )
        if "/instances" in url:
            content = b"vumark-bytes"
            return Response(
                text="",
                url=url,
                status_code=HTTPStatus.OK,
                headers={},
                request_body=data,
                tell_position=0,
                content=content,
            )
        body = '{"result_code":"Success","results":[]}'
        return Response(
            text=body,
            url=url,
            status_code=HTTPStatus.OK,
            headers={},
            request_body=data,
            tell_position=0,
            content=body.encode(),
        )


@respx.mock
def test_httpx_transport_float_timeout() -> None:
    """``HTTPXTransport`` works with a float timeout."""
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    transport = HTTPXTransport()
    response = transport(
        method="POST",
        url="https://example.com/test",
        headers={"Content-Type": "text/plain"},
        data=b"hello",
        request_timeout=30.0,
    )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK
    assert response.text == "OK"
    assert response.tell_position == len(b"OK")


@respx.mock
def test_httpx_transport_tuple_timeout() -> None:
    """``HTTPXTransport`` works with a (connect, read) timeout
    tuple.
    """
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    transport = HTTPXTransport()
    response = transport(
        method="POST",
        url="https://example.com/test",
        headers={"Content-Type": "text/plain"},
        data=b"hello",
        request_timeout=(5.0, 30.0),
    )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK


@respx.mock
def test_httpx_transport_int_timeout() -> None:
    """``HTTPXTransport`` works with an int timeout."""
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    transport = HTTPXTransport()
    response = transport(
        method="POST",
        url="https://example.com/test",
        headers={"Content-Type": "text/plain"},
        data=b"hello",
        request_timeout=30,
    )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK


@respx.mock
def test_httpx_transport_context_manager() -> None:
    """``HTTPXTransport`` can be used as a context manager."""
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    with HTTPXTransport() as transport:
        response = transport(
            method="POST",
            url="https://example.com/test",
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=30.0,
        )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
@respx.mock
async def test_async_httpx_transport_float_timeout() -> None:
    """``AsyncHTTPXTransport`` works with a float timeout."""
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    transport = AsyncHTTPXTransport()
    response = await transport(
        method="POST",
        url="https://example.com/test",
        headers={"Content-Type": "text/plain"},
        data=b"hello",
        request_timeout=30.0,
    )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK
    assert response.text == "OK"
    assert response.tell_position == len(b"OK")


@pytest.mark.asyncio
@respx.mock
async def test_async_httpx_transport_tuple_timeout() -> None:
    """``AsyncHTTPXTransport`` works with a (connect, read)
    timeout tuple.
    """
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    transport = AsyncHTTPXTransport()
    response = await transport(
        method="POST",
        url="https://example.com/test",
        headers={"Content-Type": "text/plain"},
        data=b"hello",
        request_timeout=(5.0, 30.0),
    )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
@respx.mock
async def test_async_httpx_transport_int_timeout() -> None:
    """``AsyncHTTPXTransport`` works with an int timeout."""
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    transport = AsyncHTTPXTransport()
    response = await transport(
        method="POST",
        url="https://example.com/test",
        headers={"Content-Type": "text/plain"},
        data=b"hello",
        request_timeout=30,
    )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
@respx.mock
async def test_async_httpx_transport_context_manager() -> None:
    """``AsyncHTTPXTransport`` can be used as an async context
    manager.
    """
    route = respx.post(url="https://example.com/test").mock(
        return_value=httpx.Response(
            status_code=HTTPStatus.OK,
            text="OK",
        ),
    )
    async with AsyncHTTPXTransport() as transport:
        response = await transport(
            method="POST",
            url="https://example.com/test",
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=30.0,
        )
    assert route.called
    assert isinstance(response, Response)
    assert response.status_code == HTTPStatus.OK


def test_falsy_sync_transport_is_retained(
    high_quality_image: io.BytesIO,
) -> None:
    """Falsy custom sync transports are not replaced by the default."""
    access_key = uuid.uuid4().hex
    secret_key = uuid.uuid4().hex
    transport = _FalsyTransport()
    assert not bool(transport)

    targets = VWS(
        server_access_key=access_key,
        server_secret_key=secret_key,
        transport=transport,
    ).list_targets()
    assert not bool(targets)

    query_results = CloudRecoService(
        client_access_key=access_key,
        client_secret_key=secret_key,
        transport=transport,
    ).query(image=high_quality_image)
    assert not bool(query_results)

    vumark_bytes = VuMarkService(
        server_access_key=access_key,
        server_secret_key=secret_key,
        transport=transport,
    ).generate_vumark_instance(
        target_id="target",
        instance_id="instance",
        accept=VuMarkAccept.PNG,
    )
    assert vumark_bytes == b"vumark-bytes"


@pytest.mark.asyncio
async def test_falsy_async_transport_is_retained(
    high_quality_image: io.BytesIO,
) -> None:
    """Falsy custom async transports are not replaced by the default."""
    access_key = uuid.uuid4().hex
    secret_key = uuid.uuid4().hex
    transport = _FalsyAsyncTransport()
    assert not bool(transport)

    async with AsyncVWS(
        server_access_key=access_key,
        server_secret_key=secret_key,
        transport=transport,
    ) as vws_client:
        assert not bool(await vws_client.list_targets())

    async with AsyncCloudRecoService(
        client_access_key=access_key,
        client_secret_key=secret_key,
        transport=transport,
    ) as cloud_reco_client:
        assert not bool(
            await cloud_reco_client.query(image=high_quality_image)
        )

    async with AsyncVuMarkService(
        server_access_key=access_key,
        server_secret_key=secret_key,
        transport=transport,
    ) as vumark_client:
        assert (
            await vumark_client.generate_vumark_instance(
                target_id="target",
                instance_id="instance",
                accept=VuMarkAccept.PNG,
            )
            == b"vumark-bytes"
        )


@pytest.mark.parametrize(
    argnames=("status_code", "exception_type"),
    argvalues=[
        (HTTPStatus.TOO_MANY_REQUESTS, TooManyRequestsError),
        (HTTPStatus.INTERNAL_SERVER_ERROR, ServerError),
    ],
)
@respx.mock
def test_vumark_service_handles_bodyless_http_errors(
    *,
    status_code: HTTPStatus,
    exception_type: type[ServerError | TooManyRequestsError],
) -> None:
    """VuMark HTTP errors which have no JSON body remain meaningful."""
    route = respx.post(
        url="https://example.com/targets/target/instances"
    ).mock(return_value=httpx.Response(status_code=status_code))

    with HTTPXTransport() as transport:
        service = VuMarkService(
            server_access_key="access-key",
            server_secret_key=uuid.uuid4().hex,
            base_vws_url="https://example.com",
            transport=transport,
        )
        with pytest.raises(expected_exception=exception_type):
            _ = service.generate_vumark_instance(
                target_id="target",
                instance_id="instance",
                accept=VuMarkAccept.PNG,
            )

    assert route.called


@respx.mock
def test_vws_handles_bodyless_rate_limit_response() -> None:
    """A body-less target-manager rate limit raises its specific error."""
    route = respx.get(url="https://example.com/targets").mock(
        return_value=httpx.Response(status_code=HTTPStatus.TOO_MANY_REQUESTS)
    )

    with HTTPXTransport() as transport:
        service = VWS(
            server_access_key="access-key",
            server_secret_key=uuid.uuid4().hex,
            base_vws_url="https://example.com",
            transport=transport,
        )
        with pytest.raises(expected_exception=TooManyRequestsError):
            _ = service.list_targets()

    assert route.called


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("status_code", "exception_type"),
    argvalues=[
        (HTTPStatus.TOO_MANY_REQUESTS, TooManyRequestsError),
        (HTTPStatus.INTERNAL_SERVER_ERROR, ServerError),
    ],
)
@respx.mock
async def test_async_vumark_service_handles_bodyless_http_errors(
    *,
    status_code: HTTPStatus,
    exception_type: type[ServerError | TooManyRequestsError],
) -> None:
    """Async VuMark HTTP errors without JSON remain meaningful."""
    route = respx.post(
        url="https://example.com/targets/target/instances"
    ).mock(return_value=httpx.Response(status_code=status_code))

    async with AsyncHTTPXTransport() as transport:
        service = AsyncVuMarkService(
            server_access_key="access-key",
            server_secret_key=uuid.uuid4().hex,
            base_vws_url="https://example.com",
            transport=transport,
        )
        with pytest.raises(expected_exception=exception_type):
            _ = await service.generate_vumark_instance(
                target_id="target",
                instance_id="instance",
                accept=VuMarkAccept.PNG,
            )

    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_async_vws_handles_bodyless_rate_limit_response() -> None:
    """An async target-manager rate limit raises its specific error."""
    route = respx.get(url="https://example.com/targets").mock(
        return_value=httpx.Response(status_code=HTTPStatus.TOO_MANY_REQUESTS)
    )

    async with AsyncHTTPXTransport() as transport:
        service = AsyncVWS(
            server_access_key="access-key",
            server_secret_key=uuid.uuid4().hex,
            base_vws_url="https://example.com",
            transport=transport,
        )
        with pytest.raises(expected_exception=TooManyRequestsError):
            _ = await service.list_targets()

    assert route.called
