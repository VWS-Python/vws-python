"""
Tests for `vws._request_utils`.
"""

import base64
import hmac
import hashlib

from hypothesis import given
from hypothesis.strategies import binary, text

from vws._request_utils import (
    authorization_header_for_request,
    compute_hmac_base64,
)


class TestComputeHmacBase64:
    """
    TODO
    """

    @given(key=binary(), data=binary())
    def test_compute_hmac_base64(self, key, data):
        result = compute_hmac_base64(key=key, data=data)
        decoded_result = base64.b64decode(s=result)
        hashed = hmac.new(key=key, msg=None, digestmod=hashlib.sha1)
        hashed.update(msg=data)
        assert decoded_result == hashed.digest()


class TestAuthorizationHeaderForRequest:
    """
        TODO
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
    def test_example(self, access_key, secret_key, method, content,
                     content_type, date, request_path):
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

        result = authorization_header_for_request(
            access_key=access_key,
            secret_key=secret_key,
            method=method,
            content=content,
            content_type=content_type,
            date=date,
            request_path=request_path,
        )

        assert result == expected
