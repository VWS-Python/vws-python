"""HTTP transport implementations for VWS clients.

Three transport families are available:

* ``RequestsTransport`` uses ``requests``. It is synchronous only, and
  is the default transport for the synchronous clients.
* ``HTTPXTransport`` and ``AsyncHTTPXTransport`` use ``httpx``.
  ``AsyncHTTPXTransport`` is the default transport for the
  asynchronous clients.
* ``HTTPX2Transport`` and ``AsyncHTTPX2Transport`` use ``httpx2``, the
  continuation of ``httpx`` maintained by Pydantic.

``httpx`` and ``httpx2`` are separate packages with separate client,
request, response, timeout and exception classes. Each transport uses
exactly one of them: the ``httpx`` transports raise ``httpx``
exceptions, and the ``httpx2`` transports raise ``httpx2`` exceptions.
"""

from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

import httpx
import httpx2
import requests
from beartype import BeartypeConf, beartype

from vws.response import Response

if TYPE_CHECKING:
    from collections.abc import Awaitable


@runtime_checkable
class Transport(Protocol):
    """Protocol for HTTP transports used by VWS clients.

    A transport is a callable that makes an HTTP request and
    returns a ``Response``.
    """

    def close(self) -> None:
        """Close the transport and release resources."""
        ...  # pylint: disable=unnecessary-ellipsis

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

    def close(self) -> None:
        """Close the transport.

        This is a no-op for ``RequestsTransport`` as it does not
        hold persistent connections.
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
    A single ``httpx.Client`` is reused across requests
    for connection pooling.
    """

    def __init__(self) -> None:
        """Create an ``HTTPXTransport``."""
        self._client = httpx.Client()

    def close(self) -> None:
        """Close the underlying ``httpx.Client``."""
        self._client.close()

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(self, *_args: object) -> None:
        """Exit the context manager and close the client."""
        self.close()

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
        match request_timeout:
            case tuple() as timeout:
                connect_timeout, read_timeout = timeout
                httpx_timeout = httpx.Timeout(
                    connect=connect_timeout,
                    read=read_timeout,
                    write=None,
                    pool=None,
                )
            case timeout:
                httpx_timeout = httpx.Timeout(
                    connect=timeout,
                    read=timeout,
                    write=None,
                    pool=None,
                )

        httpx_response = self._client.request(
            method=method,
            url=url,
            headers=headers,
            content=data,
            timeout=httpx_timeout,
            follow_redirects=True,
        )

        content = httpx_response.content
        request_content = httpx_response.request.content
        request_body = request_content

        return Response(
            text=httpx_response.text,
            url=str(object=httpx_response.url),
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            request_body=request_body if request_body != b"" else None,
            tell_position=len(content),
            content=content,
        )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def _httpx2_timeout(
    *,
    request_timeout: float | tuple[float, float],
) -> httpx2.Timeout:
    """The ``httpx2`` timeout for a request timeout.

    Args:
        request_timeout: The timeout for the request. A float sets
            both the connect and read timeouts. A (connect, read)
            tuple sets them individually.

    Returns:
        The equivalent ``httpx2`` timeout.
    """
    match request_timeout:
        case tuple() as timeout:
            connect_timeout, read_timeout = timeout
        case timeout:
            connect_timeout = timeout
            read_timeout = timeout

    return httpx2.Timeout(
        connect=connect_timeout,
        read=read_timeout,
        write=None,
        pool=None,
    )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def _response_from_httpx2(*, httpx2_response: httpx2.Response) -> Response:
    """Convert an ``httpx2`` response to a ``Response``.

    Args:
        httpx2_response: The response to convert.

    Returns:
        A Response populated from the ``httpx2`` response.
    """
    content = httpx2_response.content
    request_content = httpx2_response.request.content
    request_body = request_content

    return Response(
        text=httpx2_response.text,
        url=str(object=httpx2_response.url),
        status_code=httpx2_response.status_code,
        headers=dict(httpx2_response.headers),
        request_body=request_body if request_body != b"" else None,
        tell_position=len(content),
        content=content,
    )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
class HTTPX2Transport:
    """HTTP transport using the ``httpx2`` library.

    ``httpx2`` is the continuation of ``httpx`` maintained by
    Pydantic. Its client, request, response, timeout and exception
    classes are distinct from the ``httpx`` ones, so this transport
    raises ``httpx2`` exceptions, not ``httpx`` ones.
    A single ``httpx2.Client`` is reused across requests
    for connection pooling.
    """

    def __init__(self) -> None:
        """Create an ``HTTPX2Transport``."""
        self._client = httpx2.Client()

    def close(self) -> None:
        """Close the underlying ``httpx2.Client``."""
        self._client.close()

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(self, *_args: object) -> None:
        """Exit the context manager and close the client."""
        self.close()

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Make an HTTP request using ``httpx2``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            request_timeout: The request timeout.

        Returns:
            A Response populated from the ``httpx2`` response.
        """
        httpx2_response = self._client.request(
            method=method,
            url=url,
            headers=headers,
            content=data,
            timeout=_httpx2_timeout(request_timeout=request_timeout),
            follow_redirects=True,
        )
        return _response_from_httpx2(httpx2_response=httpx2_response)


@runtime_checkable
class AsyncTransport(Protocol):
    """Protocol for async HTTP transports used by VWS clients.

    An async transport is a callable that makes an HTTP request
    and returns a ``Response``.
    """

    async def aclose(self) -> None:
        """Close the transport and release resources."""
        ...  # pylint: disable=unnecessary-ellipsis

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
        match request_timeout:
            case tuple() as timeout:
                connect_timeout, read_timeout = timeout
                httpx_timeout = httpx.Timeout(
                    connect=connect_timeout,
                    read=read_timeout,
                    write=None,
                    pool=None,
                )
            case timeout:
                httpx_timeout = httpx.Timeout(
                    connect=timeout,
                    read=timeout,
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

        content = httpx_response.content
        request_content = httpx_response.request.content
        request_body = request_content

        return Response(
            text=httpx_response.text,
            url=str(object=httpx_response.url),
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            request_body=request_body if request_body != b"" else None,
            tell_position=len(content),
            content=content,
        )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
class AsyncHTTPX2Transport:
    """Async HTTP transport using the ``httpx2`` library.

    ``httpx2`` is the continuation of ``httpx`` maintained by
    Pydantic. Its client, request, response, timeout and exception
    classes are distinct from the ``httpx`` ones, so this transport
    raises ``httpx2`` exceptions, not ``httpx`` ones.
    A single ``httpx2.AsyncClient`` is reused across requests
    for connection pooling.
    """

    def __init__(self) -> None:
        """Create an ``AsyncHTTPX2Transport``."""
        self._client = httpx2.AsyncClient()

    async def aclose(self) -> None:
        """Close the underlying ``httpx2.AsyncClient``."""
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
        """Make an async HTTP request using ``httpx2``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            request_timeout: The request timeout.

        Returns:
            A Response populated from the ``httpx2`` response.
        """
        httpx2_response = await self._client.request(
            method=method,
            url=url,
            headers=headers,
            content=data,
            timeout=_httpx2_timeout(request_timeout=request_timeout),
            follow_redirects=True,
        )
        return _response_from_httpx2(httpx2_response=httpx2_response)
