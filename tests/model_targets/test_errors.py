"""Tests for Model Target errors."""

import json
from http import HTTPStatus

import pytest
from beartype import beartype

from tests.model_targets.responses import response_with_status
from vws.exceptions.model_target_exceptions import (
    ModelTargetError,
    ModelTargetOAuth2Error,
)
from vws.response import Response


@beartype
def _response(*, text: str) -> Response:
    """Get a bad-request response with a given body."""
    return response_with_status(
        text=text,
        status_code=HTTPStatus.BAD_REQUEST,
    )


@pytest.mark.parametrize(
    argnames="text",
    argvalues=[
        "",
        "Not JSON",
        "[]",
        "{}",
        '{"error": "not-an-object"}',
        '{"transaction_id": "abc", "result_code": "Fail"}',
    ],
)
def test_unknown_error_shape(*, text: str) -> None:
    """An error without a Model Target error object gives empty
    values.
    """
    error = ModelTargetError(response=_response(text=text))

    assert not bool(error.code)
    assert not bool(error.message)
    assert not bool(error.target)
    assert not bool(error.details)


def test_error_without_details() -> None:
    """An error which gives no details has no details."""
    text = json.dumps(obj={"error": {"code": "ERROR", "message": "No"}})
    error = ModelTargetError(response=_response(text=text))

    assert error.code == "ERROR"
    assert error.message == "No"
    assert not bool(error.target)
    assert not bool(error.details)


@pytest.mark.parametrize(
    argnames="text",
    argvalues=["Not JSON", "[]", "{}"],
)
def test_unknown_oauth2_error_shape(*, text: str) -> None:
    """An OAuth2 error without an error code gives empty values."""
    error = ModelTargetOAuth2Error(response=_response(text=text))

    assert not bool(error.error)
    assert not bool(error.error_description)


def test_oauth2_error_description() -> None:
    """An OAuth2 error description is given when Vuforia gives one."""
    description = "Missing or invalid authorization header"
    text = json.dumps(
        obj={
            "error": "invalid_request",
            "error_description": description,
        },
    )
    error = ModelTargetOAuth2Error(response=_response(text=text))

    assert error.error == "invalid_request"
    assert error.error_description == description
