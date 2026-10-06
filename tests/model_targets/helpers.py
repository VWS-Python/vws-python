"""Shared helpers for model targets tests."""

from http import HTTPStatus

from beartype import beartype

from vws.response import Response

# The mock accepts one hard-coded pair of Model Target Web API OAuth2
# credentials, which it does not expose.
CLIENT_ID = "client-id"
CLIENT_CREDENTIALS = ("client-id", "client-secret")


@beartype
def response_with_status(
    *,
    text: str,
    status_code: HTTPStatus,
) -> Response:
    """Get a response with a given body.

    Args:
        text: The body of the response.
        status_code: The response status code.

    Returns:
        A response with the given body.
    """
    content = text.encode(encoding="utf-8")
    return Response(
        text=text,
        url="https://vws.vuforia.com/modeltargets/datasets",
        status_code=status_code,
        headers={},
        request_body=None,
        tell_position=len(content),
        content=content,
    )
