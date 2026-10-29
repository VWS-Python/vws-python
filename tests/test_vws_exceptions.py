"""Tests for VWS exceptions."""

import uuid
from http import HTTPStatus

import pytest
from mock_vws import MockVWS, VuMarkGenerationFailure

from vws import VuMarkService
from vws.exceptions.base_exceptions import VWSError
from vws.exceptions.vws_exceptions import (
    AuthenticationFailureError,
    AuthorizationFailedError,
    BadRequestError,
    FailError,
    InvalidAcceptHeaderError,
    InvalidInstanceIdError,
    InvalidTargetTypeError,
    LicenseCheckFailedError,
    ProjectHasNoAPIAccessError,
    ProjectInactiveError,
    ProjectSuspendedError,
    QuotaExceededError,
    RequestQuotaReachedError,
    RequestTimeTooSkewedError,
    TargetStatusNotSuccessError,
    UnknownTargetError,
)
from vws.response import Response
from vws.vumark_accept import VuMarkAccept


def test_vwsexception_inheritance() -> None:
    """VWS-related exceptions should inherit from VWSException."""
    subclasses = [
        AuthenticationFailureError,
        AuthorizationFailedError,
        BadRequestError,
        FailError,
        InvalidAcceptHeaderError,
        InvalidInstanceIdError,
        InvalidTargetTypeError,
        LicenseCheckFailedError,
        ProjectInactiveError,
        ProjectHasNoAPIAccessError,
        ProjectSuspendedError,
        QuotaExceededError,
        RequestQuotaReachedError,
        RequestTimeTooSkewedError,
        TargetStatusNotSuccessError,
        UnknownTargetError,
    ]
    for subclass in subclasses:
        assert issubclass(subclass, VWSError)


def test_invalid_instance_id(
    *,
    vumark_service_client: VuMarkService,
    vumark_target_id: str,
) -> None:
    """
    An ``InvalidInstanceId`` exception is raised when an empty instance
    ID is given.
    """
    with pytest.raises(expected_exception=InvalidInstanceIdError) as exc:
        _ = vumark_service_client.generate_vumark_instance(
            target_id=vumark_target_id,
            instance_id="",
            accept=VuMarkAccept.PNG,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    argnames=("failure", "exception_type", "status_code"),
    argvalues=[
        (
            VuMarkGenerationFailure.QUOTA_EXCEEDED,
            QuotaExceededError,
            HTTPStatus.FORBIDDEN,
        ),
        (
            VuMarkGenerationFailure.LICENSE_CHECK_FAILED,
            LicenseCheckFailedError,
            HTTPStatus.FORBIDDEN,
        ),
        (
            VuMarkGenerationFailure.AUTHORIZATION_FAILED,
            AuthorizationFailedError,
            HTTPStatus.UNAUTHORIZED,
        ),
    ],
)
def test_documented_vumark_error_codes(
    *,
    failure: VuMarkGenerationFailure,
    exception_type: type[VWSError],
    status_code: HTTPStatus,
) -> None:
    """Documented VuMark failures raise matching exceptions."""
    with MockVWS(vumark_generation_failure=failure):
        vumark_service = VuMarkService(
            server_access_key=uuid.uuid4().hex,
            server_secret_key=uuid.uuid4().hex,
        )

        with pytest.raises(expected_exception=exception_type) as exc:
            _ = vumark_service.generate_vumark_instance(
                target_id="exampletargetid",
                instance_id="example_instance_id",
                accept=VuMarkAccept.PNG,
            )

    assert exc.value.response.status_code == status_code
    assert failure.value in exc.value.response.text


def test_vwserror_from_result_code() -> None:
    """``VWSError.from_result_code`` returns the mapped exception."""
    response = Response(
        text='{"result_code":"UnknownTarget"}',
        url="https://example.com/targets/123",
        status_code=HTTPStatus.NOT_FOUND,
        headers={},
        request_body=None,
        tell_position=0,
        content=b"",
    )

    exception = VWSError.from_result_code(
        result_code="UnknownTarget",
        response=response,
    )

    assert isinstance(exception, UnknownTargetError)
    assert exception.response is response


def test_project_has_no_api_access_casing() -> None:
    """The ``ProjectHasNoApiAccess`` result code, as spelled in Vuforia's
    result codes table, maps to ``ProjectHasNoAPIAccessError``.
    """
    result_code = "ProjectHasNoApiAccess"
    response = Response(
        text=f'{{"result_code":"{result_code}"}}',
        url="https://example.com/targets",
        status_code=HTTPStatus.FORBIDDEN,
        headers={},
        request_body=None,
        tell_position=0,
        content=b"",
    )

    exception = VWSError.from_result_code(
        result_code=result_code,
        response=response,
    )

    assert isinstance(exception, ProjectHasNoAPIAccessError)


@pytest.mark.parametrize(
    argnames=("exception_type", "url"),
    argvalues=[
        (UnknownTargetError, "https://vws.vuforia.com/targets/abc"),
        (UnknownTargetError, "https://example.com/prefix/targets/abc"),
        (UnknownTargetError, "https://example.com/prefix/summary/abc"),
        (UnknownTargetError, "https://example.com/prefix/duplicates/abc"),
        (
            TargetStatusNotSuccessError,
            "https://vws.vuforia.com/targets/abc",
        ),
        (
            TargetStatusNotSuccessError,
            "https://example.com/prefix/targets/abc",
        ),
        (
            TargetStatusNotSuccessError,
            "https://example.com/prefix/targets/abc/instances",
        ),
    ],
)
def test_target_id_with_base_url_prefixes(
    *,
    exception_type: type[UnknownTargetError | TargetStatusNotSuccessError],
    url: str,
) -> None:
    """``target_id`` is correct even when ``base_vws_url`` has a path
    prefix.
    """
    response = Response(
        text="{}",
        url=url,
        status_code=HTTPStatus.NOT_FOUND,
        headers={},
        request_body=None,
        tell_position=0,
        content=b"",
    )
    assert exception_type(response=response).target_id == "abc"


def test_target_id_missing_from_url() -> None:
    """A clear error is raised when the response URL has no target ID."""
    response = Response(
        text="{}",
        url="https://example.com/no-target-here",
        status_code=HTTPStatus.NOT_FOUND,
        headers={},
        request_body=None,
        tell_position=0,
        content=b"",
    )
    with pytest.raises(
        expected_exception=ValueError,
        match="Could not find a target ID",
    ):
        _ = UnknownTargetError(response=response).target_id
