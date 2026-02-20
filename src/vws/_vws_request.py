"""Internal helper for making authenticated requests to the Vuforia Target
API.
"""

from urllib.parse import urljoin

import requests
from beartype import BeartypeConf, beartype
from vws_auth_tools import authorization_header, rfc_1123_date

from vws.response import Response


@beartype(conf=BeartypeConf(is_pep484_tower=True))
def target_api_request(
    *,
    content_type: str,
    server_access_key: str,
    server_secret_key: str,
    method: str,
    data: bytes,
    request_path: str,
    base_vws_url: str,
    request_timeout_seconds: float | tuple[float, float],
    extra_headers: dict[str, str],
) -> Response:
    """Make a request to the Vuforia Target API.

    This uses `requests` to make a request against https://vws.vuforia.com.

    Args:
        content_type: The content type of the request.
        server_access_key: A VWS server access key.
        server_secret_key: A VWS server secret key.
        method: The HTTP method which will be used in the request.
        data: The request body which will be used in the request.
        request_path: The path to the endpoint which will be used in the
            request.
        base_vws_url: The base URL for the VWS API.
        request_timeout_seconds: The timeout for the request, as used by
            ``requests.request``. This can be a float to set both the
            connect and read timeouts, or a (connect, read) tuple.
        extra_headers: Additional headers to include in the request.

    Returns:
        The response to the request made by `requests`.
    """
    date_string = rfc_1123_date()

    signature_string = authorization_header(
        access_key=server_access_key,
        secret_key=server_secret_key,
        method=method,
        content=data,
        content_type=content_type,
        date=date_string,
        request_path=request_path,
    )

    headers = {
        "Authorization": signature_string,
        "Date": date_string,
        "Content-Type": content_type,
        **extra_headers,
    }

    url = urljoin(base=base_vws_url, url=request_path)

    requests_response = requests.request(
        method=method,
        url=url,
        headers=headers,
        data=data,
        timeout=request_timeout_seconds,
    )

    return Response(
        text=requests_response.text,
        url=requests_response.url,
        status_code=requests_response.status_code,
        headers=dict(requests_response.headers),
        request_body=requests_response.request.body,
        tell_position=requests_response.raw.tell(),
        content=bytes(requests_response.content),
    )
