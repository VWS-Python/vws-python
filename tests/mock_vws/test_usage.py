"""
Tests for the usage of the mock.
"""

import base64
import io
import socket

import pytest
import requests
from hypothesis import given
from hypothesis.strategies import text
from requests import codes
from requests_mock.exceptions import NoMockAddress

from mock_vws import MockVWS
from tests.mock_vws.utils import (
    add_target_to_vws,
    database_summary,
    get_vws_target,
)
from tests.utils import VuforiaServerCredentials
from vws._request_utils import rfc_1123_date


def request_unmocked_address() -> None:
    """
    Make a request, using `requests` to an unmocked, free local address.

    Raises:
        requests.exceptions.ConnectionError: This is expected as there is
            nothing to connect to.
        requests_mock.exceptions.NoMockAddress: This request is being made in
            the context of a `requests_mock` mock which does not mock local
            addresses.
    """
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    address = 'http://localhost:{free_port}'.format(free_port=port)
    requests.get(address)


def request_mocked_address() -> None:
    """
    Make a request, using `requests` to an address that is mocked `MockVWS`.
    """
    requests.get(
        url='https://vws.vuforia.com/summary',
        headers={
            'Date': rfc_1123_date(),
            'Authorization': 'bad_auth_token',
        },
        data=b'',
    )


class TestUsage:
    """
    Tests for usage patterns of the mock.
    """

    @MockVWS()
    def test_decorator(self) -> None:
        """
        Using the mock as a decorator stops any requests made with `requests`
        to non-Vuforia addresses, but not to mocked Vuforia endpoints.
        """
        with pytest.raises(NoMockAddress):
            request_unmocked_address()

        # No exception is raised when making a request to a mocked endpoint.
        request_mocked_address()

    @MockVWS(real_http=True)
    def test_decorator_real_http(self) -> None:
        """
        When the `real_http` parameter given to the decorator is set to `True`,
        requests made to unmocked addresses are not stopped.
        """
        with pytest.raises(requests.exceptions.ConnectionError):
            request_unmocked_address()

    def test_context_manager(self) -> None:
        """
        Using the mock as a context manager stops any requests made with
        `requests` to non-Vuforia addresses, but not to mocked Vuforia
        endpoints.
        """
        with MockVWS():
            with pytest.raises(NoMockAddress):
                request_unmocked_address()

            # No exception is raised when making a request to a mocked
            # endpoint.
            request_mocked_address()

        # The mocking stops when the context manager stops.
        with pytest.raises(requests.exceptions.ConnectionError):
            request_unmocked_address()

    def test_real_http(self) -> None:
        """
        When the `real_http` parameter given to the context manager is set to
        `True`, requests made to unmocked addresses are not stopped.
        """
        with MockVWS(real_http=True):
            with pytest.raises(requests.exceptions.ConnectionError):
                request_unmocked_address()


class TestDatabaseName:
    """
    Tests for the database name.
    """

    def test_default(
        self, vuforia_server_credentials: VuforiaServerCredentials
    ) -> None:
        """
        By default, the database has a random name.
        """
        with MockVWS():
            response = database_summary(
                vuforia_server_credentials=vuforia_server_credentials,
            )
            first_database_name = response.json()['name']

        with MockVWS():
            response = database_summary(
                vuforia_server_credentials=vuforia_server_credentials,
            )
            second_database_name = response.json()['name']

        assert first_database_name != second_database_name

    @given(database_name=text())
    def test_custom_name(
        self,
        database_name: str,
        vuforia_server_credentials: VuforiaServerCredentials
    ) -> None:
        """
        It is possible to set a custom database name.
        """
        with MockVWS(database_name=database_name):
            response = database_summary(
                vuforia_server_credentials=vuforia_server_credentials,
            )
            assert response.json()['name'] == database_name


class TestPersistence:
    """
    Tests for usage patterns of the mock.
    """

    def test_context_manager(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        When the context manager is used, targets are not persisted between
        invocations.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        with MockVWS():
            response = add_target_to_vws(
                vuforia_server_credentials=vuforia_server_credentials,
                data=data,
            )

            target_id = response.json()['target_id']

            response = get_vws_target(
                vuforia_server_credentials=vuforia_server_credentials,
                target_id=target_id,
            )

            assert response.status_code == codes.OK

        with MockVWS():
            response = get_vws_target(
                vuforia_server_credentials=vuforia_server_credentials,
                target_id=target_id,
            )

            assert response.status_code == codes.NOT_FOUND

    def test_decorator(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb: io.BytesIO,
    ) -> None:
        """
        When the decorator is used, targets are not persisted between
        invocations.
        """
        image_data = png_rgb.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'example',
            'width': 1,
            'image': image_data_encoded,
        }

        @MockVWS()
        def create() -> str:
            """
            Create a new target and return its id.
            """
            response = add_target_to_vws(
                vuforia_server_credentials=vuforia_server_credentials,
                data=data,
            )

            target_id = response.json()['target_id']

            response = get_vws_target(
                vuforia_server_credentials=vuforia_server_credentials,
                target_id=target_id,
            )

            assert response.status_code == codes.OK
            return target_id

        @MockVWS()
        def verify(target_id: str) -> None:
            """
            Assert that there is no target with the given id.
            """
            response = get_vws_target(
                vuforia_server_credentials=vuforia_server_credentials,
                target_id=target_id,
            )

            assert response.status_code == codes.NOT_FOUND

        target_id = create()
        verify(target_id=target_id)


class TestCredentials:
    """
    XXX
    """

    def test_default(self) -> None:
        pass

    def test_custom_credentials(self) -> None:
        pass
