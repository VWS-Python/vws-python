"""JSON value types used by Vuforia API requests and responses."""

type JSONValue = (
    bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None
)
"""A value which can be represented in a JSON document."""
