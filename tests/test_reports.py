"""Tests for public report constructors."""

import pytest

from vws.reports import QueryResult

type JSONValue = (
    bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None
)


@pytest.mark.parametrize(
    argnames="response",
    argvalues=[
        {"target_id": 1},
        {
            "target_id": "target-id",
            "target_data": {
                "name": "target-name",
                "application_metadata": None,
                "target_timestamp": True,
            },
        },
        {
            "target_id": "target-id",
            "target_data": {
                "name": "target-name",
                "application_metadata": 1,
                "target_timestamp": 0,
            },
        },
    ],
)
def test_query_result_rejects_invalid_response_values(
    *,
    response: dict[str, JSONValue],
) -> None:
    """Query reports reject values of the wrong type."""
    with pytest.raises(expected_exception=TypeError):
        _ = QueryResult.from_response_dict(response_dict=response)
