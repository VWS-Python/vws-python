"""Responses for exceptions."""

from dataclasses import dataclass


@dataclass
class Response:
    """
    A response from a request.
    """

    text: str
    url: str
    status_code: int
    headers: dict[str, str]
    request_body: bytes | str | None
