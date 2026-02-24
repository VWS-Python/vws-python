"""HTTP transport implementations for VWS clients."""

from typing import Protocol, runtime_checkable

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
        timeout: float | tuple[float, float],
    ) -> Response:
        """Make an HTTP request.

        Args:
            method: The HTTP method (e.g. "GET", "POST").
            url: The full URL to request.
            headers: Headers to send with the request.
            data: The request body as bytes.
            timeout: The timeout for the request. A float
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
        timeout: float | tuple[float, float],
    ) -> Response:
        """Make an HTTP request using ``requests``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            timeout: The request timeout.

        Returns:
            A Response populated from the requests response.
        """
        requests_response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=timeout,
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
        timeout: float | tuple[float, float],
    ) -> Response:
        """Make an HTTP request using ``httpx``.

        Args:
            method: The HTTP method.
            url: The full URL.
            headers: Request headers.
            data: The request body.
            timeout: The request timeout.

        Returns:
            A Response populated from the httpx response.
        """
        if isinstance(timeout, tuple):
            connect_timeout, read_timeout = timeout
            httpx_timeout = httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=None,
                pool=None,
            )
        else:
            httpx_timeout = httpx.Timeout(timeout=timeout)

        httpx_response = httpx.request(
            method=method,
            url=url,
            headers=headers,
            content=data,
            timeout=httpx_timeout,
        )

        return Response(
            text=httpx_response.text,
            url=str(object=httpx_response.url),
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            request_body=bytes(httpx_response.request.content),
            tell_position=0,
            content=bytes(httpx_response.content),
        )
