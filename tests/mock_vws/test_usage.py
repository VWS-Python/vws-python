"""
Tests for the usage of the mock.
"""

import socket

import pytest
import requests
from requests_mock.exceptions import NoMockAddress

from mock_vws import MockVWS
from vws._request_utils import rfc_1123_date


def request_unmocked_address() -> None:
    """
    Make a request, using `requests` to an unmocked, free local address.

    Raises:
        requests.exceptions.ConnectionError: This is expected as there is
            nothing to connect to.
        requests_mock.exceptions.NoMockAddress: This request is being made in
            the context of a `requests_mock` mock which does not mocl local
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
