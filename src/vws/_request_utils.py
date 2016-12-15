"""
Utilities for making requests to Vuforia.

Based on Python examples from https://developer.vuforia.com/downloads/samples.
"""

import hashlib
import hmac
import base64


def compute_md5_hex(data: bytes):
    """Return the hex MD5 of the data"""
    h = hashlib.md5()
    h.update(data)
    return h.hexdigest()


def compute_hmac_base64(key: bytes, data: bytes) -> bytes:
    """Return the Base64 encoded HMAC-SHA1 using the provide key"""
    hashed = hmac.new(key=key, msg=None, digestmod=hashlib.sha1)
    hashed.update(msg=data)
    return base64.b64encode(s=hashed.digest())


def authorization_header_for_request(access_key: str, secret_key: bytes,
                                     method: str, content: bytes,
                                     content_type: str, date: str,
                                     request_path: str) -> bytes:
    """Return the value of the Authorization header for the request parameters

    TODO Args, Return
    """
    components_to_sign = list()
    components_to_sign.append(method)
    components_to_sign.append(str(compute_md5_hex(content)))
    components_to_sign.append(str(content_type))
    components_to_sign.append(str(date))
    components_to_sign.append(str(request_path))
    string_to_sign = "\n".join(components_to_sign)
    string_to_sign = bytes(string_to_sign, encoding='ascii')
    signature = compute_hmac_base64(key=secret_key, data=string_to_sign)
    auth_header = "VWS %s:%s" % (access_key, signature)
    return auth_header
