"""
Tests for `vws._request_utils`.
"""

import base64
import datetime
import hashlib
import hmac
import re

from typing import Pattern
from urllib.parse import urljoin

import wrapt
import requests_mock

from freezegun import freeze_time
from hypothesis import given
from hypothesis.strategies import binary, text
from requests import codes
from requests_mock import GET

from vws._request_utils import (
    authorization_header,
    compute_hmac_base64,
    rfc_1123_date,
    target_api_request,
)


class TestComputeHmacBase64:
    """
    Test for `compute_hmac_base64`.
    """

    @given(key=binary(), data=binary())
    def test_compute_hmac_base64(self, key, data):
        """
        This is mostly a reimplementation of the hash computation. The real
        test is that making requests works. This exists to make refactoring
        easier as we can check that the output is as expected.
        """
        result = compute_hmac_base64(key=key, data=data)
        decoded_result = base64.b64decode(s=result)
        hashed = hmac.new(key=key, msg=None, digestmod=hashlib.sha1)
        hashed.update(msg=data)
        assert decoded_result == hashed.digest()

    def test_example(self):
        """
        A know example is hashed to the expected value.
        """
        result = compute_hmac_base64(key=b'my_key', data=b'my_data')
        assert result == b'nUa8YOjTBsRCXNk0UgPHS3sq+w0='


class TestRfc1123FormatDate:
    """
    Tests for ``rfc_1123_date``.
    """

    def test_rfc_1123_date(self):
        """
        ``rfc_1123_date`` returns the date formatted as required by Vuforia.
        This test matches the example date set at
        https://library.vuforia.com/articles/Training/Using-the-VWS-API.
        """
        date = datetime.datetime(
            day=22,
            month=4,
            year=2012,
            hour=8,
            minute=49,
            second=37,
        )
        with freeze_time(date):
            assert rfc_1123_date() == 'Sun, 22 Apr 2012 08:49:37 GMT'


class TestAuthorizationHeader:
    """
    Tests for `authorization_header`.
    """

    @given(
        access_key=binary(),
        secret_key=binary(),
        method=text(),
        content=binary(),
        content_type=text(),
        date=text(),
        request_path=text(),
    )
    def test_authorization_header(self, access_key, secret_key, method,
                                  content, content_type, date, request_path):
        """
        This is mostly a reimplimentation of the header creation. The real
        test is that the header works. This exists to make refactoring easier
        as we can check that the output is as expected.
        """
        hashed = hashlib.md5()
        hashed.update(content)
        content_hex = hashed.hexdigest()

        string = bytes(method, encoding='utf-8')
        string += b'\n'
        string += bytes(content_hex, encoding='utf-8')
        string += b'\n'
        string += bytes(content_type, encoding='utf-8')
        string += b'\n'
        string += bytes(date, encoding='utf-8')
        string += b'\n'
        string += bytes(request_path, encoding='utf-8')

        signature = compute_hmac_base64(key=secret_key, data=string)

        expected = (
            b'VWS ' + access_key + b':' + signature
        )

        result = authorization_header(
            access_key=access_key,
            secret_key=secret_key,
            method=method,
            content=content,
            content_type=content_type,
            date=date,
            request_path=request_path,
        )

        assert result == expected

    def test_example(self):
        """
        Test a successful example of creating an Authorization header.
        """
        result = authorization_header(
            access_key=b'my_access_key',
            secret_key=b'my_secret_key',
            method='GET',
            content=b'{"something": "other"}',
            content_type='text/example',
            date='Sun, 22 Apr 2012 08:49:37 GMT.',
            request_path='/example_path',
        )

        assert result == b'VWS my_access_key:CetfV6Yl/3mSz/Xl0c+O1YjXKYg='


def _endpoint_pattern(path_pattern: str) -> Pattern:
    """Given a path pattern, return a regex which will match URLs to
    patch.

    Args:
        TODO
    """
    base = 'https://vws.vuforia.com/'
    joined = urljoin(base=base, url=path_pattern)
    return re.compile(joined)


class FakeVuforia:
    """
    TODO
    """

    DATABASE_SUMMARY_URL = _endpoint_pattern(path_pattern='summary')

    def __init__(self, access_key: str, secret_key: str) -> None:
        """
        Args:
            access_key: A VWS access key.
            secret_key: A VWS secret key.

        Attributes:
            access_key: A VWS access key.
            secret_key: A VWS secret key.
        """
        self.access_key = 'blah_access_key'  # type: str
        self.secret_key = 'blah_secret_key'  # type: str

    def database_summary(self, request, context):
        """
        TODO
        """
        # Assert against requests.headers
        return "in Mock"


@wrapt.decorator
def mock_vuforia(wrapped, instance, args,  # pylint: disable=unused-argument
                 kwargs):
    """
    Route requests to Vuforia's Web Service APIs to fakes of those APIs.
    """
    # TODO Document args, types
    # Create a mock which verifies the signature
    # TODO This should have the same access and secrets as the env vars, so
    # they need to be set.
    fake_vuforia = FakeVuforia(access_key='access', secret_key='secret')
    with requests_mock.Mocker(real_http=True) as req:
        req.register_uri(
            method=GET,
            url=fake_vuforia.DATABASE_SUMMARY_URL,
            text=fake_vuforia.database_summary,
            status_code=codes.INTERNAL_SERVER_ERROR,
        )
        return wrapped(*args, **kwargs)


class TestTargetAPIRequest:

    """TODO"""

    def test_success(self, vuforia_server_credentials):
        """TODO"""
        method = 'GET'
        content = b''
        content_type = 'application/json'
        request_path = "/summary"

        response = target_api_request(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=method,
            content=content,
            content_type=content_type,
            request_path=request_path
        )
        assert response.status_code == codes.OK

    @mock_vuforia
    def test_success_req(self):
        """TODO"""
        # TODO Use constantly for HTTP request handling,
        # not str
        method = 'GET'
        content = b''
        content_type = 'application/json'
        request_path = "/summary"

        response = target_api_request(
            access_key=b'vuforia_server_credentials.access_key',
            secret_key=b'vuforia_server_credentials.secret_key',
            method=method,
            content=content,
            content_type=content_type,
            request_path=request_path
        )
        assert response.text == 'in Mock'
        assert response.status_code == codes.INTERNAL_SERVER_ERROR
