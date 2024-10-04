"""Responses for requests to VWS and VWQ."""

from dataclasses import dataclass

from beartype import beartype


@dataclass(frozen=True)
@beartype
class Response:
    """
    A response from a request.
    """

    text: str
    url: str
    status_code: int
    headers: dict[str, str]
    request_body: bytes | str | None
    tell_position: int
