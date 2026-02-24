"""Tests for HTTP transport implementations."""

from http import HTTPStatus

import httpx
import pytest
import respx

from vws import AsyncCloudRecoService, AsyncVuMarkService, AsyncVWS
from vws.response import Response
from vws.transports import AsyncHTTPXTransport, HTTPXTransport


class TestHTTPXTransport:
    """Tests for ``HTTPXTransport``."""

    @staticmethod
    @respx.mock
    def test_float_timeout() -> None:
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

    @staticmethod
    @respx.mock
    def test_tuple_timeout() -> None:
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


class TestAsyncHTTPXTransport:
    """Tests for ``AsyncHTTPXTransport``."""

    @staticmethod
    @pytest.mark.asyncio
    @respx.mock
    async def test_float_timeout() -> None:
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

    @staticmethod
    @pytest.mark.asyncio
    @respx.mock
    async def test_tuple_timeout() -> None:
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

    @staticmethod
    @pytest.mark.asyncio
    @respx.mock
    async def test_context_manager() -> None:
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


class _NoCloseTransport:
    """A minimal async transport without ``aclose``."""

    async def __call__(  # pragma: no cover
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Not implemented."""
        raise NotImplementedError


_DUMMY_KEY = "x"


class TestAsyncClientAclose:
    """Tests for ``aclose`` on async clients with transports that
    lack ``aclose``.
    """

    @staticmethod
    @pytest.mark.asyncio
    async def test_vws_aclose_no_transport_aclose() -> None:
        """``AsyncVWS.aclose`` works when the transport has no
        ``aclose``.
        """
        client = AsyncVWS(
            server_access_key=_DUMMY_KEY,
            server_secret_key=_DUMMY_KEY,
            transport=_NoCloseTransport(),
        )
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_cloud_reco_aclose_no_transport_aclose() -> None:
        """``AsyncCloudRecoService.aclose`` works when the transport
        has no ``aclose``.
        """
        client = AsyncCloudRecoService(
            client_access_key=_DUMMY_KEY,
            client_secret_key=_DUMMY_KEY,
            transport=_NoCloseTransport(),
        )
        await client.aclose()

    @staticmethod
    @pytest.mark.asyncio
    async def test_vumark_aclose_no_transport_aclose() -> None:
        """``AsyncVuMarkService.aclose`` works when the transport
        has no ``aclose``.
        """
        client = AsyncVuMarkService(
            server_access_key=_DUMMY_KEY,
            server_secret_key=_DUMMY_KEY,
            transport=_NoCloseTransport(),
        )
        await client.aclose()
