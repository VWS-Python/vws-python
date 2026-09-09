"""Internal helper for making authenticated requests to the Vuforia Target
API.
"""

from beartype import BeartypeConf, beartype
from vws_auth_tools import authorization_header, rfc_1123_date

from vws.response import Response
from vws.transports import Transport


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
    transport: Transport,
) -> Response:
    """Make a request to the Vuforia Target API.

    Args:
        content_type: The content type of the request.
        server_access_key: A VWS server access key.
        server_secret_key: A VWS server secret key.
        method: The HTTP method which will be used in the
            request.
        data: The request body which will be used in the
            request.
        request_path: The path to the endpoint which will be
            used in the request.
        base_vws_url: The base URL for the VWS API.
        request_timeout_seconds: The timeout for the request.
            This can be a float to set both the connect and
            read timeouts, or a (connect, read) tuple.
        extra_headers: Additional headers to include in the
            request.
        transport: The HTTP transport to use for the request.

    Returns:
        The response to the request.
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

    url = base_vws_url.rstrip("/") + request_path

    return transport(
        method=method,
        url=url,
        headers=headers,
        data=data,
        request_timeout=request_timeout_seconds,
    )
