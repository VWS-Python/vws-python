"""
Tests for `vws._request_utils`.
"""

import base64
import hmac
import hashlib

from hypothesis import given
from hypothesis.strategies import binary

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

    def test_example(self):

        access_key = 'a'
        secret_key = b'b'
        method = 'c'
        content = b'content'
        content_type = 'application/json'
        date = 'date'
        request_path = 'rp'

        hashed = hashlib.md5()
        hashed.update(content)
        content_hex = hashed.hexdigest()

        string = bytes(method, encoding='ascii')
        string += b'\n'
        string += bytes(content_hex, encoding='ascii')
        string += b'\n'
        string += bytes(content_type, encoding='ascii')
        string += b'\n'
        string += bytes(date, encoding='ascii')
        string += b'\n'
        string += bytes(request_path, encoding='ascii')

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
