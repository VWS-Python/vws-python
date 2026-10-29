"""Tests for `httpx` transports."""

from __future__ import annotations

import uuid
from http import HTTPStatus

import httpx
import pytest
import respx

from vws import (
    AsyncVuMarkService,
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
        return Response(
            text="",
            url=url,
            status_code=HTTPStatus.OK,
            headers={},
            request_body=data,
            tell_position=0,
            content=b"vumark-bytes",
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
        return Response(
            text="",
            url=url,
            status_code=HTTPStatus.OK,
            headers={},
            request_body=data,
            tell_position=0,
            content=b"vumark-bytes",
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


def test_falsy_sync_transport_is_retained() -> None:
    """Falsy custom sync transports are not replaced by the default."""
    access_key = uuid.uuid4().hex
    secret_key = uuid.uuid4().hex
    transport = _FalsyTransport()
    assert not bool(transport)

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
async def test_falsy_async_transport_is_retained() -> None:
    """Falsy custom async transports are not replaced by the default."""
    access_key = uuid.uuid4().hex
    secret_key = uuid.uuid4().hex
    transport = _FalsyAsyncTransport()
    assert not bool(transport)

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
