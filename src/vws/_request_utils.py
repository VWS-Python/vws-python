"""
Utilities for making requests to Vuforia.

Based on Python examples from https://developer.vuforia.com/downloads/samples.
"""

import base64
import email.utils
import hashlib
import hmac


def compute_hmac_base64(key: bytes, data: bytes) -> bytes:
    """
    Return the Base64 encoded HMAC-SHA1 hash of the given `data` using the
    provided `key`.
    """
    hashed = hmac.new(key=key, msg=None, digestmod=hashlib.sha1)
    hashed.update(msg=data)
    return base64.b64encode(s=hashed.digest())


def rfc_1123_date() -> str:
    """
    Return the date formatted as per RFC 2616, section 3.3.1, rfc1123-date, as
    described in
    https://library.vuforia.com/articles/Training/Using-the-VWS-API.
    """
    return email.utils.formatdate(None, localtime=False, usegmt=True)


def authorization_header(  # pylint: disable=too-many-arguments

        access_key: bytes,
        secret_key: bytes,
        method: str,
        content: bytes,
        content_type: str,
        date: str,
        request_path: str
) -> bytes:
    """
    Return an `Authorization` header which can be used for a request made to
    the VWS API with the given attributes.

    Args:
        access_key: A VWS access key.
        secret_key: A VWS secret key.
        method: The HTTP method which will be used in the request.
        content: The request body which will be used in the request.
        content_type: The `Content-Type` header which will be used in the
            request.
        date: The current date which must exactly match the date sent in the
            `Date` header.
        request_path: The path to the endpoint which will be used in the
            request.
    """
    hashed = hashlib.md5()
    hashed.update(content)
    content_md5_hex = hashed.hexdigest()

    components_to_sign = [
        method,
        content_md5_hex,
        content_type,
        date,
        request_path,
    ]
    string_to_sign = "\n".join(components_to_sign)
    signature = compute_hmac_base64(
        key=secret_key,
        data=bytes(
            string_to_sign,
            encoding='utf-8',
        ),
    )
    auth_header = b"VWS %s:%s" % (access_key, signature)
    return auth_header
