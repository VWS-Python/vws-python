"""
Tests for the usage of the mock.
"""

import base64
import io
import socket
import string
import uuid

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


def assert_valid_credentials(access_key: str, secret_key: str):
    """
    Given credentials, assert that they can authenticate with a Vuforia
    database.

    Raises:
        AssertionError: The given credentials fail to authenticate with a
            Vuforia database.
    """
    credentials = VuforiaServerCredentials(
        database_name=uuid.uuid4().hex,
        access_key=access_key,
        secret_key=secret_key,
    )

    response = get_vws_target(
        vuforia_server_credentials=credentials,
        target_id=uuid.uuid4().hex,
    )

    # This shows that the response does not give an authentication
    # error which is what would happen if the keys were incorrect.
    assert response.status_code == codes.NOT_FOUND


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

    def test_default(self) -> None:
        """
        By default, the database has a random name.
        """
        with MockVWS() as mock:
            vuforia_server_credentials = VuforiaServerCredentials(
                database_name=uuid.uuid4().hex,
                access_key=mock.access_key,
                secret_key=mock.secret_key,
            )

            response = database_summary(
                vuforia_server_credentials=vuforia_server_credentials,
            )
            first_database_name = response.json()['name']

        with MockVWS() as mock:
            vuforia_server_credentials = VuforiaServerCredentials(
                database_name=uuid.uuid4().hex,
                access_key=mock.access_key,
                secret_key=mock.secret_key,
            )
            response = database_summary(
                vuforia_server_credentials=vuforia_server_credentials,
            )
            second_database_name = response.json()['name']

        assert first_database_name != second_database_name

    @given(database_name=text())
    def test_custom_name(
        self,
        database_name: str,
    ) -> None:
        """
        It is possible to set a custom database name.
        """
        with MockVWS(database_name=database_name) as mock:
            vuforia_server_credentials = VuforiaServerCredentials(
                database_name=database_name,
                access_key=mock.access_key,
                secret_key=mock.secret_key,
            )
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

        with MockVWS() as mock:
            vuforia_server_credentials = VuforiaServerCredentials(
                database_name=uuid.uuid4().hex,
                access_key=mock.access_key,
                secret_key=mock.secret_key,
            )

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

        with MockVWS() as mock:
            vuforia_server_credentials = VuforiaServerCredentials(
                database_name=uuid.uuid4().hex,
                access_key=mock.access_key,
                secret_key=mock.secret_key,
            )

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

        @MockVWS(
            access_key=vuforia_server_credentials.access_key.decode('ascii'),
            secret_key=vuforia_server_credentials.secret_key.decode('ascii'),
        )
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

        @MockVWS(
            access_key=vuforia_server_credentials.access_key.decode('ascii'),
            secret_key=vuforia_server_credentials.secret_key.decode('ascii'),
        )
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
    Tests for setting credentials for the mock.
    """

    def test_default(self) -> None:
        """
        By default the mock uses a random access key and secret key.
        """
        with MockVWS() as mock:
            first_access_key = mock.access_key
            first_secret_key = mock.secret_key

        with MockVWS() as mock:
            assert mock.access_key != first_access_key
            assert mock.secret_key != first_secret_key

    # We limit this to ASCII letters because some characters are not allowed
    # in request headers (e.g. a leading space).
    @given(
        access_key=text(alphabet=string.ascii_letters),
        secret_key=text(alphabet=string.ascii_letters)
    )
    def test_custom_credentials(
        self, access_key: str, secret_key: str
    ) -> None:
        """
        It is possible to set custom credentials.
        """
        with MockVWS(access_key=access_key, secret_key=secret_key) as mock:
            assert mock.access_key == access_key
            assert mock.secret_key == secret_key
            assert_valid_credentials(
                access_key=access_key, secret_key=secret_key
            )

    @MockVWS()
    def test_credentials_passed(
        self, access_key: str, secret_key: str
    ) -> None:
        """
        XXX
        """
        assert_valid_credentials(access_key=access_key, secret_key=secret_key)

    @MockVWS()
    def test_with_pytest_fixtures(
        self,
        access_key: str,
        secret_key: str,
        vuforia_server_credentials: VuforiaServerCredentials,
    ) -> None:
        """
        XXX
        """
        assert_valid_credentials(access_key=access_key, secret_key=secret_key)

    @given(hypothesis_variable=text())
    @MockVWS()
    def test_with_hypothesis(
        self, access_key: str, secret_key: str, hypothesis_variable: str
    ) -> None:
        """
        XXX
        """
        assert_valid_credentials(access_key=access_key, secret_key=secret_key)

    @MockVWS()
    def test_with_defaults(
        self, access_key: str, secret_key: str, thing: int=1
    ) -> None:
        """
        XXX
        """
        assert_valid_credentials(access_key=access_key, secret_key=secret_key)

    def test_with_other_variables(self) -> None:
        """
        XXX
        """
        @MockVWS()
        def func(access_key: str, secret_key: str, other_var: int) -> None:
            """
            XXX
            """
            assert_valid_credentials(
                access_key=access_key, secret_key=secret_key
            )

    def test_missing_vars(self) -> None:
        """
        XXX
        """
        @MockVWS
        def func() -> None:
            """
            XXX
            """
            pass
