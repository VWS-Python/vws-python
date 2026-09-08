"""Tests for HTTP transport implementations."""

import io  # noqa: TC003
import uuid
from http import HTTPStatus

import httpx
import httpx2
import pytest
import respx
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase, VuMarkDatabase
from mock_vws.target import VuMarkTarget

from vws import (
    VWS,
    AsyncCloudRecoService,
    AsyncModelTargetService,
    AsyncVuMarkService,
    AsyncVWS,
    CloudRecoService,
    ModelTargetService,
    VuMarkService,
)
from vws.model_target_datasets import (
    ModelTargetDatasetType,
    ModelTargetModel,
)
from vws.reports import ModelTargetDatasetStatuses, TargetStatuses
from vws.response import Response
from vws.transports import (
    AsyncHTTPX2Transport,
    AsyncHTTPXTransport,
    HTTPX2Transport,
    HTTPXTransport,
)
from vws.vumark_accept import VuMarkAccept


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

    @staticmethod
    @respx.mock
    def test_int_timeout() -> None:
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

    @staticmethod
    @respx.mock
    def test_context_manager() -> None:
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
    async def test_int_timeout() -> None:
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


# The mock accepts one hard-coded pair of Model Target Web API OAuth2
# credentials, which it does not expose.
_MODEL_TARGET_CLIENT_ID = "client-id"
_MODEL_TARGET_CLIENT_SECRET = "client-secret"  # noqa: S105

_HTTPX2_URL = "https://example.com/test"
_HTTPX2_REFUSED_URL = "https://example.com/refused"


@pytest.fixture(name="httpx2_requests")
def fixture_httpx2_requests(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> list[httpx2.Request]:
    """Answer every ``httpx2`` request with a fake server, and collect the
    requests which it sees.

    The fake server answers ``OK`` to every request except those for
    ``_HTTPX2_REFUSED_URL``, which it refuses to connect to.
    """
    requests_seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        """Answer an ``httpx2`` request.

        Args:
            request: The request to answer.

        Returns:
            An ``OK`` response.

        Raises:
            httpx2.ConnectError: The request is for the refused URL.
        """
        requests_seen.append(request)
        if str(object=request.url) == _HTTPX2_REFUSED_URL:
            raise httpx2.ConnectError(
                message="Connection refused",
                request=request,
            )
        return httpx2.Response(
            status_code=HTTPStatus.OK,
            text="OK",
            headers={"X-Example": "example"},
        )

    mock_transport = httpx2.MockTransport(handler=handler)

    class _Client(httpx2.Client):
        """A synchronous client which uses the fake server."""

        def __init__(self) -> None:
            """Create a client which uses the fake server."""
            super().__init__(transport=mock_transport)

    class _AsyncClient(httpx2.AsyncClient):
        """An asynchronous client which uses the fake server."""

        def __init__(self) -> None:
            """Create a client which uses the fake server."""
            super().__init__(transport=mock_transport)

    monkeypatch.setattr(target=httpx2, name="Client", value=_Client)
    monkeypatch.setattr(target=httpx2, name="AsyncClient", value=_AsyncClient)
    return requests_seen


class TestHTTPX2Transport:
    """Tests for ``HTTPX2Transport``."""

    @staticmethod
    def test_float_timeout(httpx2_requests: list[httpx2.Request]) -> None:
        """``HTTPX2Transport`` works with a float timeout.

        A float sets both the connect and read timeouts, and the response
        is converted in full.
        """
        transport = HTTPX2Transport()
        response = transport(
            method="POST",
            url=_HTTPX2_URL,
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=30.0,
        )
        (request,) = httpx2_requests
        assert request.extensions["timeout"] == {
            "connect": 30.0,
            "read": 30.0,
            "write": None,
            "pool": None,
        }
        assert request.headers["Content-Type"] == "text/plain"
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK
        assert response.text == "OK"
        assert response.url == _HTTPX2_URL
        assert response.headers["x-example"] == "example"
        assert response.request_body == b"hello"
        assert response.content == b"OK"
        assert response.tell_position == len(b"OK")

    @staticmethod
    def test_tuple_timeout(httpx2_requests: list[httpx2.Request]) -> None:
        """``HTTPX2Transport`` works with a (connect, read) timeout
        tuple.
        """
        transport = HTTPX2Transport()
        response = transport(
            method="POST",
            url=_HTTPX2_URL,
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=(5.0, 30.0),
        )
        (request,) = httpx2_requests
        assert request.extensions["timeout"] == {
            "connect": 5.0,
            "read": 30.0,
            "write": None,
            "pool": None,
        }
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK

    @staticmethod
    def test_int_timeout(httpx2_requests: list[httpx2.Request]) -> None:
        """``HTTPX2Transport`` works with an int timeout."""
        transport = HTTPX2Transport()
        response = transport(
            method="POST",
            url=_HTTPX2_URL,
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=30,
        )
        (request,) = httpx2_requests
        assert request.extensions["timeout"] == {
            "connect": 30,
            "read": 30,
            "write": None,
            "pool": None,
        }
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK

    @staticmethod
    def test_empty_body(httpx2_requests: list[httpx2.Request]) -> None:
        """An empty request body is reported as ``None``, as it is for
        the ``requests`` and ``httpx`` transports.
        """
        transport = HTTPX2Transport()
        response = transport(
            method="GET",
            url=_HTTPX2_URL,
            headers={},
            data=b"",
            request_timeout=30.0,
        )
        assert len(httpx2_requests) == 1
        assert response.request_body is None

    @staticmethod
    def test_context_manager(httpx2_requests: list[httpx2.Request]) -> None:
        """``HTTPX2Transport`` can be used as a context manager, and
        leaving the context closes the client.
        """
        with HTTPX2Transport() as transport:
            response = transport(
                method="POST",
                url=_HTTPX2_URL,
                headers={"Content-Type": "text/plain"},
                data=b"hello",
                request_timeout=30.0,
            )
        assert len(httpx2_requests) == 1
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK

        with pytest.raises(
            expected_exception=RuntimeError,
            match="client has been closed",
        ):
            _ = transport(
                method="POST",
                url=_HTTPX2_URL,
                headers={"Content-Type": "text/plain"},
                data=b"hello",
                request_timeout=30.0,
            )

    @staticmethod
    def test_close(httpx2_requests: list[httpx2.Request]) -> None:
        """Closing the transport closes the client."""
        transport = HTTPX2Transport()
        transport.close()
        with pytest.raises(
            expected_exception=RuntimeError,
            match="client has been closed",
        ):
            _ = transport(
                method="POST",
                url=_HTTPX2_URL,
                headers={"Content-Type": "text/plain"},
                data=b"hello",
                request_timeout=30.0,
            )
        assert not bool(httpx2_requests)

    @staticmethod
    def test_httpx2_exceptions(httpx2_requests: list[httpx2.Request]) -> None:
        """Errors are raised as ``httpx2`` exceptions, which are not
        ``httpx`` exceptions.
        """
        transport = HTTPX2Transport()
        with pytest.raises(expected_exception=httpx2.ConnectError) as exc:
            _ = transport(
                method="GET",
                url=_HTTPX2_REFUSED_URL,
                headers={},
                data=b"",
                request_timeout=30.0,
            )
        assert len(httpx2_requests) == 1
        assert not isinstance(exc.value, httpx.HTTPError)


class TestAsyncHTTPX2Transport:
    """Tests for ``AsyncHTTPX2Transport``."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_float_timeout(
        httpx2_requests: list[httpx2.Request],
    ) -> None:
        """``AsyncHTTPX2Transport`` works with a float timeout.

        A float sets both the connect and read timeouts, and the response
        is converted in full.
        """
        transport = AsyncHTTPX2Transport()
        response = await transport(
            method="POST",
            url=_HTTPX2_URL,
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=30.0,
        )
        (request,) = httpx2_requests
        assert request.extensions["timeout"] == {
            "connect": 30.0,
            "read": 30.0,
            "write": None,
            "pool": None,
        }
        assert request.headers["Content-Type"] == "text/plain"
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK
        assert response.text == "OK"
        assert response.url == _HTTPX2_URL
        assert response.headers["x-example"] == "example"
        assert response.request_body == b"hello"
        assert response.content == b"OK"
        assert response.tell_position == len(b"OK")

    @staticmethod
    @pytest.mark.asyncio
    async def test_tuple_timeout(
        httpx2_requests: list[httpx2.Request],
    ) -> None:
        """``AsyncHTTPX2Transport`` works with a (connect, read)
        timeout tuple.
        """
        transport = AsyncHTTPX2Transport()
        response = await transport(
            method="POST",
            url=_HTTPX2_URL,
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=(5.0, 30.0),
        )
        (request,) = httpx2_requests
        assert request.extensions["timeout"] == {
            "connect": 5.0,
            "read": 30.0,
            "write": None,
            "pool": None,
        }
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK

    @staticmethod
    @pytest.mark.asyncio
    async def test_int_timeout(
        httpx2_requests: list[httpx2.Request],
    ) -> None:
        """``AsyncHTTPX2Transport`` works with an int timeout."""
        transport = AsyncHTTPX2Transport()
        response = await transport(
            method="POST",
            url=_HTTPX2_URL,
            headers={"Content-Type": "text/plain"},
            data=b"hello",
            request_timeout=30,
        )
        (request,) = httpx2_requests
        assert request.extensions["timeout"] == {
            "connect": 30,
            "read": 30,
            "write": None,
            "pool": None,
        }
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK

    @staticmethod
    @pytest.mark.asyncio
    async def test_empty_body(
        httpx2_requests: list[httpx2.Request],
    ) -> None:
        """An empty request body is reported as ``None``, as it is for
        the ``requests`` and ``httpx`` transports.
        """
        transport = AsyncHTTPX2Transport()
        response = await transport(
            method="GET",
            url=_HTTPX2_URL,
            headers={},
            data=b"",
            request_timeout=30.0,
        )
        assert len(httpx2_requests) == 1
        assert response.request_body is None

    @staticmethod
    @pytest.mark.asyncio
    async def test_context_manager(
        httpx2_requests: list[httpx2.Request],
    ) -> None:
        """``AsyncHTTPX2Transport`` can be used as an async context
        manager, and leaving the context closes the client.
        """
        async with AsyncHTTPX2Transport() as transport:
            response = await transport(
                method="POST",
                url=_HTTPX2_URL,
                headers={"Content-Type": "text/plain"},
                data=b"hello",
                request_timeout=30.0,
            )
        assert len(httpx2_requests) == 1
        assert isinstance(response, Response)
        assert response.status_code == HTTPStatus.OK

        with pytest.raises(
            expected_exception=RuntimeError,
            match="client has been closed",
        ):
            await transport(
                method="POST",
                url=_HTTPX2_URL,
                headers={"Content-Type": "text/plain"},
                data=b"hello",
                request_timeout=30.0,
            )

    @staticmethod
    @pytest.mark.asyncio
    async def test_aclose(httpx2_requests: list[httpx2.Request]) -> None:
        """Closing the transport closes the client."""
        transport = AsyncHTTPX2Transport()
        await transport.aclose()
        with pytest.raises(
            expected_exception=RuntimeError,
            match="client has been closed",
        ):
            await transport(
                method="POST",
                url=_HTTPX2_URL,
                headers={"Content-Type": "text/plain"},
                data=b"hello",
                request_timeout=30.0,
            )
        assert not bool(httpx2_requests)

    @staticmethod
    @pytest.mark.asyncio
    async def test_httpx2_exceptions(
        httpx2_requests: list[httpx2.Request],
    ) -> None:
        """Errors are raised as ``httpx2`` exceptions, which are not
        ``httpx`` exceptions.
        """
        transport = AsyncHTTPX2Transport()
        with pytest.raises(expected_exception=httpx2.ConnectError) as exc:
            await transport(
                method="GET",
                url=_HTTPX2_REFUSED_URL,
                headers={},
                data=b"",
                request_timeout=30.0,
            )
        assert len(httpx2_requests) == 1
        assert not isinstance(exc.value, httpx.HTTPError)


class TestHTTPX2TransportWithMock:
    """Tests for synchronous clients using ``HTTPX2Transport`` against
    the mock.
    """

    @staticmethod
    def test_vws_and_cloud_reco(high_quality_image: io.BytesIO) -> None:
        """A target can be added with ``VWS`` and found with
        ``CloudRecoService``.
        """
        database = CloudDatabase()
        with (
            MockVWS(processing_time_seconds=0.2) as mock,
            HTTPX2Transport() as transport,
        ):
            mock.add_cloud_database(cloud_database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
                transport=transport,
            )
            cloud_reco_client = CloudRecoService(
                client_access_key=database.client_access_key,
                client_secret_key=database.client_secret_key,
                transport=transport,
            )
            target_id = vws_client.add_target(
                name="example",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )
            vws_client.wait_for_target_processed(target_id=target_id)
            target_record = vws_client.get_target_record(target_id=target_id)
            assert target_record.status == TargetStatuses.SUCCESS

            (match,) = cloud_reco_client.query(image=high_quality_image)
            assert match.target_id == target_id

    @staticmethod
    def test_vumark() -> None:
        """A VuMark instance can be generated with ``VuMarkService``."""
        vumark_target = VuMarkTarget(name="vumark-template")
        database = VuMarkDatabase(vumark_targets={vumark_target})
        with MockVWS() as mock, HTTPX2Transport() as transport:
            mock.add_vumark_database(vumark_database=database)
            vumark_client = VuMarkService(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
                transport=transport,
            )
            vumark_bytes = vumark_client.generate_vumark_instance(
                target_id=vumark_target.target_id,
                instance_id="instance",
                accept=VuMarkAccept.PNG,
            )
        assert vumark_bytes.startswith(b"\x89PNG")

    @staticmethod
    def test_model_targets(model_target_model: ModelTargetModel) -> None:
        """A Model Target dataset can be generated with
        ``ModelTargetService``.
        """
        with (
            MockVWS(processing_time_seconds=0.2),
            HTTPX2Transport() as transport,
        ):
            model_target_client = ModelTargetService(
                client_id=_MODEL_TARGET_CLIENT_ID,
                client_secret=_MODEL_TARGET_CLIENT_SECRET,
                transport=transport,
            )
            dataset_uuid = model_target_client.create_dataset(
                name="dataset",
                target_sdk="11.0",
                models=[model_target_model],
                dataset_type=ModelTargetDatasetType.STANDARD,
            )
            report = model_target_client.wait_for_dataset_generated(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )
            assert report.status == ModelTargetDatasetStatuses.DONE
            model_target_client.delete_dataset(
                dataset_uuid=dataset_uuid,
                dataset_type=ModelTargetDatasetType.STANDARD,
            )

    @staticmethod
    @pytest.mark.parametrize(
        argnames="custom_timeout",
        argvalues=[0.1, (5.0, 0.1)],
        ids=["float", "tuple"],
    )
    def test_timeout(custom_timeout: float | tuple[float, float]) -> None:
        """A response which takes longer than the read timeout raises an
        ``httpx2`` timeout.
        """
        database = CloudDatabase()
        sleeps: list[float] = []
        with MockVWS(
            response_delay_seconds=0.11,
            sleep_fn=sleeps.append,
        ) as mock:
            mock.add_cloud_database(cloud_database=database)
            with HTTPX2Transport() as transport:
                vws_client = VWS(
                    server_access_key=database.server_access_key,
                    server_secret_key=database.server_secret_key,
                    request_timeout_seconds=custom_timeout,
                    transport=transport,
                )
                with pytest.raises(expected_exception=httpx2.ReadTimeout):
                    _ = vws_client.list_targets()
                # The mock sleeps for the read timeout before raising.
                assert sleeps == [0.1]


async def _add_and_query_target(
    *,
    database: CloudDatabase,
    transport: AsyncHTTPX2Transport,
    image: io.BytesIO,
) -> None:
    """Add a target with ``AsyncVWS`` and find it with
    ``AsyncCloudRecoService``.

    Args:
        database: The mock database to add the target to.
        transport: The transport for the clients to use.
        image: The image to add as a target and then query with.
    """
    vws_client = AsyncVWS(
        server_access_key=database.server_access_key,
        server_secret_key=database.server_secret_key,
        transport=transport,
    )
    cloud_reco_client = AsyncCloudRecoService(
        client_access_key=database.client_access_key,
        client_secret_key=database.client_secret_key,
        transport=transport,
    )
    target_id = await vws_client.add_target(
        name="example",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    await vws_client.wait_for_target_processed(target_id=target_id)
    target_record = await vws_client.get_target_record(target_id=target_id)
    assert target_record.status == TargetStatuses.SUCCESS

    (match,) = await cloud_reco_client.query(image=image)
    assert match.target_id == target_id


async def _generate_dataset(
    *,
    transport: AsyncHTTPX2Transport,
    model_target_model: ModelTargetModel,
) -> None:
    """Generate, wait for and delete a Model Target dataset with
    ``AsyncModelTargetService``.

    Args:
        transport: The transport for the client to use.
        model_target_model: The model to generate a dataset from.
    """
    model_target_client = AsyncModelTargetService(
        client_id=_MODEL_TARGET_CLIENT_ID,
        client_secret=_MODEL_TARGET_CLIENT_SECRET,
        transport=transport,
    )
    dataset_uuid = await model_target_client.create_dataset(
        name="dataset",
        target_sdk="11.0",
        models=[model_target_model],
        dataset_type=ModelTargetDatasetType.STANDARD,
    )
    report = await model_target_client.wait_for_dataset_generated(
        dataset_uuid=dataset_uuid,
        dataset_type=ModelTargetDatasetType.STANDARD,
    )
    assert report.status == ModelTargetDatasetStatuses.DONE
    await model_target_client.delete_dataset(
        dataset_uuid=dataset_uuid,
        dataset_type=ModelTargetDatasetType.STANDARD,
    )


class TestAsyncHTTPX2TransportWithMock:
    """Tests for asynchronous clients using ``AsyncHTTPX2Transport``
    against the mock.
    """

    @staticmethod
    @pytest.mark.asyncio
    async def test_vws_and_cloud_reco(high_quality_image: io.BytesIO) -> None:
        """A target can be added with ``AsyncVWS`` and found with
        ``AsyncCloudRecoService``.
        """
        database = CloudDatabase()
        with MockVWS(processing_time_seconds=0.2) as mock:
            mock.add_cloud_database(cloud_database=database)
            async with AsyncHTTPX2Transport() as transport:
                await _add_and_query_target(
                    database=database,
                    transport=transport,
                    image=high_quality_image,
                )

    @staticmethod
    @pytest.mark.asyncio
    async def test_vumark() -> None:
        """A VuMark instance can be generated with
        ``AsyncVuMarkService``.
        """
        vumark_target = VuMarkTarget(name="vumark-template")
        database = VuMarkDatabase(vumark_targets={vumark_target})
        with MockVWS() as mock:
            mock.add_vumark_database(vumark_database=database)
            async with AsyncHTTPX2Transport() as transport:
                vumark_client = AsyncVuMarkService(
                    server_access_key=database.server_access_key,
                    server_secret_key=database.server_secret_key,
                    transport=transport,
                )
                vumark_bytes = await vumark_client.generate_vumark_instance(
                    target_id=vumark_target.target_id,
                    instance_id="instance",
                    accept=VuMarkAccept.PNG,
                )
        assert vumark_bytes.startswith(b"\x89PNG")

    @staticmethod
    @pytest.mark.asyncio
    async def test_model_targets(model_target_model: ModelTargetModel) -> None:
        """A Model Target dataset can be generated with
        ``AsyncModelTargetService``.
        """
        with MockVWS(processing_time_seconds=0.2):
            async with AsyncHTTPX2Transport() as transport:
                await _generate_dataset(
                    transport=transport,
                    model_target_model=model_target_model,
                )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        argnames="custom_timeout",
        argvalues=[0.1, (5.0, 0.1)],
        ids=["float", "tuple"],
    )
    async def test_timeout(
        custom_timeout: float | tuple[float, float],
    ) -> None:
        """A response which takes longer than the read timeout raises an
        ``httpx2`` timeout.
        """
        database = CloudDatabase()
        sleeps: list[float] = []
        with MockVWS(
            response_delay_seconds=0.11,
            sleep_fn=sleeps.append,
        ) as mock:
            mock.add_cloud_database(cloud_database=database)
            async with AsyncHTTPX2Transport() as transport:
                vws_client = AsyncVWS(
                    server_access_key=database.server_access_key,
                    server_secret_key=database.server_secret_key,
                    request_timeout_seconds=custom_timeout,
                    transport=transport,
                )
                with pytest.raises(expected_exception=httpx2.ReadTimeout):
                    await vws_client.list_targets()
                # The mock sleeps for the read timeout before raising.
                assert sleeps == [0.1]
