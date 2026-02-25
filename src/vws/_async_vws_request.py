"""Internal helper for making authenticated async requests to the
Vuforia Target API.
"""

from beartype import BeartypeConf, beartype

from vws._vws_request import build_vws_request_args
from vws.response import Response
from vws.transports import AsyncTransport


@beartype(conf=BeartypeConf(is_pep484_tower=True))
async def async_target_api_request(
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
    transport: AsyncTransport,
) -> Response:
    """Make an async request to the Vuforia Target API.

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
        transport: The async HTTP transport to use for the
            request.

    Returns:
        The response to the request.
    """
    url, headers = build_vws_request_args(
        content_type=content_type,
        server_access_key=server_access_key,
        server_secret_key=server_secret_key,
        method=method,
        data=data,
        request_path=request_path,
        base_vws_url=base_vws_url,
        extra_headers=extra_headers,
    )

    return await transport(
        method=method,
        url=url,
        headers=headers,
        data=data,
        request_timeout=request_timeout_seconds,
    )
