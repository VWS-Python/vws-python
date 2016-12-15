"""
Tests for `vws._request_utils`.
"""

import base64
import datetime
import hashlib
import hmac

from freezegun import freeze_time
from hypothesis import given
from hypothesis.strategies import binary, text

from vws._request_utils import (
    authorization_header,
    compute_hmac_base64,
    rfc_1123_date,
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
        access_key=text(),
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

        expected = 'VWS ' + access_key + ':' + str(signature)

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
