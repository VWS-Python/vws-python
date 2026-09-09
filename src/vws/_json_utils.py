"""Validation helpers for JSON received from remote services."""

import json
from typing import TypeGuard


def _is_json_object(value: object, /) -> TypeGuard[dict[str, object]]:
    """Return whether a decoded JSON value is an object."""
    return isinstance(value, dict)


def _is_object_list(value: object, /) -> TypeGuard[list[object]]:
    """Return whether a decoded JSON value is an array."""
    return isinstance(value, list)


def _validated_object(*, value: object) -> dict[str, object]:
    """Return a decoded JSON object."""
    if not _is_json_object(value):
        msg = "Expected a JSON object."
        raise TypeError(msg)
    return value


def json_object(*, value: str | bytes | bytearray) -> dict[str, object]:
    """Decode and validate a JSON object."""
    loaded: object = json.loads(s=value)
    return _validated_object(value=loaded)


def object_field(*, value: dict[str, object], name: str) -> dict[str, object]:
    """Return a required JSON object field."""
    return _validated_object(value=value[name])


def string_value(*, value: object, name: str) -> str:
    """Return a JSON value after validating that it is a string."""
    if not isinstance(value, str):
        msg = f"{name} must be a string."
        raise TypeError(msg)
    return value


def string_field(*, value: dict[str, object], name: str) -> str:
    """Return a required string field from a JSON object."""
    return string_value(value=value[name], name=name)


def string_list_field(
    *,
    value: dict[str, object],
    name: str,
) -> list[str]:
    """Return a required list of strings from a JSON object."""
    items = value[name]
    if not _is_object_list(items) or not all(
        isinstance(item, str) for item in items
    ):
        msg = f"{name} must be a list of strings."
        raise TypeError(msg)
    return [item for item in items if isinstance(item, str)]


def object_list_field(
    *,
    value: dict[str, object],
    name: str,
) -> list[dict[str, object]]:
    """Return a required list of JSON objects."""
    items = value[name]
    if not _is_object_list(items):
        msg = f"{name} must be a list of JSON objects."
        raise TypeError(msg)
    return [_validated_object(value=item) for item in items]
