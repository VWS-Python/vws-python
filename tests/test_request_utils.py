"""
Tests for `vws._request_utils`.
"""

from vws._request_utils import authorization_header_for_request


class TestAuthorizationHeaderForRequest:
    """
        TODO
        """

    def test_example(self):
        expected = (
            "X"
        )

        access_key = 'a'
        secret_key = b'b'
        method = 'c'
        content = b'content'
        content_type = 'application/json'
        date = 'date'
        request_path = 'rp'

        assert authorization_header_for_request(
            access_key=access_key,
            secret_key=secret_key,
            method=method,
            content=content,
            content_type=content_type,
            date=date,
            request_path=request_path,
        ) == expected
