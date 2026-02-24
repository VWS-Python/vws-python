"""Tests for HTTP transport implementations."""

from http import HTTPStatus

import httpx
import respx

from vws.response import Response
from vws.transports import HTTPXTransport


class TestHTTPXTransport:
    """Tests for ``HTTPXTransport``."""

    @staticmethod
    @respx.mock
    def test_float_timeout() -> None:
        """``HTTPXTransport`` works with a float timeout."""
        respx.post(url="https://example.com/test").mock(
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
            timeout=30.0,
        )
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
        respx.post(url="https://example.com/test").mock(
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
            timeout=(5.0, 30.0),
        )
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK
