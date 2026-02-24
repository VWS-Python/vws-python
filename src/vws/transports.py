"""HTTP transport implementations for VWS clients."""

from collections.abc import Awaitable
from typing import Protocol, Self, runtime_checkable

import httpx
import requests
from beartype import BeartypeConf, beartype

from vws.response import Response


@runtime_checkable
class Transport(Protocol):
    """Protocol for HTTP transports used by VWS clients.

    A transport is a callable that makes an HTTP request and
    returns a ``Response``.
    """

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Make an HTTP request.

        Args:
            method: The HTTP method (e.g. "GET", "POST").
            url: The full URL to request.
            headers: Headers to send with the request.
            data: The request body as bytes.
            request_timeout: The timeout for the request. A float
                sets both the connect and read timeouts. A
                (connect, read) tuple sets them individually.

        Returns:
            A Response populated from the HTTP response.
        """
        ...  # pylint: disable=unnecessary-ellipsis


@beartype(conf=BeartypeConf(is_pep484_tower=True))
class RequestsTransport:
    """HTTP transport using the ``requests`` library.

    This is the default transport.
    """

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Make an HTTP request using ``requests``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            request_timeout: The request timeout.

        Returns:
            A Response populated from the requests response.
        """
        requests_response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=request_timeout,
        )

        return Response(
            text=requests_response.text,
            url=requests_response.url,
            status_code=requests_response.status_code,
            headers=dict(requests_response.headers),
            request_body=requests_response.request.body,
            tell_position=requests_response.raw.tell(),
            content=bytes(requests_response.content),
        )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
class HTTPXTransport:
    """HTTP transport using the ``httpx`` library.

    Use this transport for environments where ``httpx`` is
    preferred over ``requests``.
    """

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Make an HTTP request using ``httpx``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            request_timeout: The request timeout.

        Returns:
            A Response populated from the httpx response.
        """
        if isinstance(request_timeout, tuple):
            connect_timeout, read_timeout = request_timeout
            httpx_timeout = httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=None,
                pool=None,
            )
        else:
            httpx_timeout = httpx.Timeout(
                connect=request_timeout,
                read=request_timeout,
                write=None,
                pool=None,
            )

        httpx_response = httpx.request(
            method=method,
            url=url,
            headers=headers,
            content=data,
            timeout=httpx_timeout,
            follow_redirects=True,
        )

        content = bytes(httpx_response.content)
        request_content = httpx_response.request.content

        return Response(
            text=httpx_response.text,
            url=str(object=httpx_response.url),
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            request_body=bytes(request_content) or None,
            tell_position=len(content),
            content=content,
        )


@runtime_checkable
class AsyncTransport(Protocol):
    """Protocol for async HTTP transports used by VWS clients.

    An async transport is a callable that makes an HTTP request
    and returns a ``Response``.
    """

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Awaitable[Response]:
        """Make an async HTTP request.

        Args:
            method: The HTTP method (e.g. "GET", "POST").
            url: The full URL to request.
            headers: Headers to send with the request.
            data: The request body as bytes.
            request_timeout: The timeout for the request. A float
                sets both the connect and read timeouts. A
                (connect, read) tuple sets them individually.

        Returns:
            A Response populated from the HTTP response.
        """
        ...  # pylint: disable=unnecessary-ellipsis


@beartype(conf=BeartypeConf(is_pep484_tower=True))
class AsyncHTTPXTransport:
    """Async HTTP transport using the ``httpx`` library.

    This is the default transport for async VWS clients.
    A single ``httpx.AsyncClient`` is reused across requests
    for connection pooling.
    """

    def __init__(self) -> None:
        """Create an ``AsyncHTTPXTransport``."""
        self._client = httpx.AsyncClient()

    async def aclose(self) -> None:
        """Close the underlying ``httpx.AsyncClient``."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *_args: object) -> None:
        """Exit the async context manager and close the client."""
        await self.aclose()

    async def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Make an async HTTP request using ``httpx``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            request_timeout: The request timeout.

        Returns:
            A Response populated from the httpx response.
        """
        if isinstance(request_timeout, tuple):
            connect_timeout, read_timeout = request_timeout
            httpx_timeout = httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=None,
                pool=None,
            )
        else:
            httpx_timeout = httpx.Timeout(
                connect=request_timeout,
                read=request_timeout,
                write=None,
                pool=None,
            )

        httpx_response = await self._client.request(
            method=method,
            url=url,
            headers=headers,
            content=data,
            timeout=httpx_timeout,
            follow_redirects=True,
        )

        content = bytes(httpx_response.content)
        request_content = httpx_response.request.content

        return Response(
            text=httpx_response.text,
            url=str(object=httpx_response.url),
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            request_body=bytes(request_content) or None,
            tell_position=len(content),
            content=content,
        )
