"""Tests for HTTP transport implementations."""

from http import HTTPStatus

import httpx
import pytest
import respx

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
