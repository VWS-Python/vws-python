"""Tests for VWS exceptions."""

import io
import uuid
from http import HTTPStatus

import pytest
from freezegun import freeze_time
from mock_vws import MockVWS, VuMarkGenerationFailure
from mock_vws.database import CloudDatabase
from mock_vws.states import States

from vws import VWS, VuMarkService
from vws.exceptions.base_exceptions import VWSError
from vws.exceptions.custom_exceptions import (
    ServerError,
)
from vws.exceptions.vws_exceptions import (
    AuthenticationFailureError,
    AuthorizationFailedError,
    BadImageError,
    BadRequestError,
    DateRangeError,
    FailError,
    ImageTooLargeError,
    InvalidAcceptHeaderError,
    InvalidInstanceIdError,
    InvalidTargetTypeError,
    LicenseCheckFailedError,
    MetadataTooLargeError,
    ProjectHasNoAPIAccessError,
    ProjectInactiveError,
    ProjectSuspendedError,
    QuotaExceededError,
    RequestQuotaReachedError,
    RequestTimeTooSkewedError,
    TargetNameExistError,
    TargetQuotaReachedError,
    TargetStatusNotSuccessError,
    TargetStatusProcessingError,
    UnknownTargetError,
)
from vws.response import Response
from vws.vumark_accept import VuMarkAccept


def test_image_too_large(
    *,
    vws_client: VWS,
    png_too_large: io.BytesIO | io.BufferedRandom,
) -> None:
    """
    When giving an image which is too large, an ``ImageTooLarge``
    exception
    is
    raised.
    """
    with pytest.raises(expected_exception=ImageTooLargeError) as exc:
        vws_client.add_target(
            name="x",
            width=1,
            image=png_too_large,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_invalid_given_id(vws_client: VWS) -> None:
    """
    Giving an invalid ID to a helper which requires a target ID to be
    given
    causes an ``UnknownTarget`` exception to be raised.
    """
    target_id = "12345abc"
    with pytest.raises(expected_exception=UnknownTargetError) as exc:
        vws_client.delete_target(target_id=target_id)
    assert exc.value.response.status_code == HTTPStatus.NOT_FOUND
    assert exc.value.target_id == target_id


def test_add_bad_name(
    *,
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    When a name with a bad character is given, a ``ServerError``
    exception
    is
    raised.
    """
    max_char_value = 65535
    bad_name = chr(max_char_value + 1)
    with pytest.raises(
        expected_exception=ServerError,
    ) as exc:
        vws_client.add_target(
            name=bad_name,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


def test_request_quota_reached() -> None:
    """A ``RequestQuotaReached`` exception is raised at the quota."""
    database = CloudDatabase(request_quota=0)
    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        with pytest.raises(expected_exception=RequestQuotaReachedError) as exc:
            vws_client.list_targets()

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


def test_target_quota_reached(high_quality_image: io.BytesIO) -> None:
    """A ``TargetQuotaReached`` exception is raised at the quota."""
    database = CloudDatabase(target_quota=0)
    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        with pytest.raises(expected_exception=TargetQuotaReachedError) as exc:
            vws_client.add_target(
                name="x",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    argnames=("state", "expected_exception"),
    argvalues=[
        (States.PROJECT_SUSPENDED, ProjectSuspendedError),
        (States.PROJECT_HAS_NO_API_ACCESS, ProjectHasNoAPIAccessError),
    ],
)
def test_project_state_error(
    *,
    state: States,
    expected_exception: type[VWSError],
) -> None:
    """Configured project states raise their matching exceptions."""
    database = CloudDatabase(state=state)
    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        with pytest.raises(expected_exception=expected_exception) as exc:
            vws_client.list_targets()

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


def test_fail(high_quality_image: io.BytesIO) -> None:
    """A ``Fail`` exception is raised when the server access key does not
    exist.
    """
    with MockVWS():
        vws_client = VWS(
            server_access_key=uuid.uuid4().hex,
            server_secret_key=uuid.uuid4().hex,
        )

        with pytest.raises(expected_exception=FailError) as exc:
            vws_client.add_target(
                name="x",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == HTTPStatus.BAD_REQUEST


def test_bad_image(vws_client: VWS) -> None:
    """A ``BadImage`` exception is raised when a non-image is given."""
    not_an_image = io.BytesIO(initial_bytes=b"Not an image")
    with pytest.raises(expected_exception=BadImageError) as exc:
        vws_client.add_target(
            name="x",
            width=1,
            image=not_an_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_target_name_exist(
    *,
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetNameExist`` exception is raised after adding two targets
    with
    the
    same name.
    """
    vws_client.add_target(
        name="x",
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )
    with pytest.raises(expected_exception=TargetNameExistError) as exc:
        vws_client.add_target(
            name="x",
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN
    assert exc.value.target_name == "x"


def test_project_inactive(
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``ProjectInactive`` exception is raised if adding a target to an
    inactive
    database.
    """
    database = CloudDatabase(state=States.PROJECT_INACTIVE)
    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        with pytest.raises(expected_exception=ProjectInactiveError) as exc:
            vws_client.add_target(
                name="x",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


def test_target_status_processing(
    *,
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetStatusProcessing`` exception is raised if trying to delete
    a
    target which is processing.
    """
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )

    with pytest.raises(expected_exception=TargetStatusProcessingError) as exc:
        vws_client.delete_target(target_id=target_id)

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN
    assert exc.value.target_id == target_id


def test_metadata_too_large(
    *,
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``MetadataTooLarge`` exception is raised if the metadata given is
    too
    large.
    """
    with pytest.raises(expected_exception=MetadataTooLargeError) as exc:
        vws_client.add_target(
            name="x",
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata="a" * 1024 * 1024 * 10,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_request_time_too_skewed(
    *,
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``RequestTimeTooSkewed`` exception is raised when the request time
    is
    more than five minutes different from the server time.
    """
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )

    vws_max_time_skew = 60 * 5
    leeway = 10
    time_difference_from_now = vws_max_time_skew + leeway

    # We use a custom tick because we expect the following:
    #
    # * At least one time check when creating the request
    # * At least one time check when processing the request
    #
    # >= 1 ticks are acceptable.
    with (
        freeze_time(auto_tick_seconds=time_difference_from_now),
        pytest.raises(expected_exception=RequestTimeTooSkewedError) as exc,
    ):
        vws_client.get_target_record(target_id=target_id)

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN


def test_authentication_failure(
    high_quality_image: io.BytesIO,
) -> None:
    """
    An ``AuthenticationFailure`` exception is raised when the server
    access
    key
    exists but the server secret key is incorrect, or when a client key is
    incorrect.
    """
    database = CloudDatabase()

    vws_client = VWS(
        server_access_key=database.server_access_key,
        server_secret_key=uuid.uuid4().hex,
    )

    with MockVWS() as mock:
        mock.add_cloud_database(cloud_database=database)

        with pytest.raises(
            expected_exception=AuthenticationFailureError
        ) as exc:
            vws_client.add_target(
                name="x",
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED


def test_target_status_not_success(
    *,
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetStatusNotSuccess`` exception is raised when updating a
    target
    which has a status which is not "Success".
    """
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )

    with pytest.raises(expected_exception=TargetStatusNotSuccessError) as exc:
        vws_client.update_target(target_id=target_id)

    assert exc.value.response.status_code == HTTPStatus.FORBIDDEN
    assert exc.value.target_id == target_id


def test_vwsexception_inheritance() -> None:
    """VWS-related exceptions should inherit from VWSException."""
    subclasses = [
        AuthenticationFailureError,
        AuthorizationFailedError,
        BadImageError,
        BadRequestError,
        DateRangeError,
        FailError,
        ImageTooLargeError,
        InvalidAcceptHeaderError,
        InvalidInstanceIdError,
        InvalidTargetTypeError,
        LicenseCheckFailedError,
        MetadataTooLargeError,
        ProjectInactiveError,
        ProjectHasNoAPIAccessError,
        ProjectSuspendedError,
        QuotaExceededError,
        RequestQuotaReachedError,
        RequestTimeTooSkewedError,
        TargetNameExistError,
        TargetQuotaReachedError,
        TargetStatusNotSuccessError,
        TargetStatusProcessingError,
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
        vumark_service_client.generate_vumark_instance(
            target_id=vumark_target_id,
            instance_id="",
            accept=VuMarkAccept.PNG,
        )

    assert exc.value.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_invalid_target_type(
    high_quality_image: io.BytesIO,
) -> None:
    """
    An ``InvalidTargetType`` exception is raised when trying to generate
    a VuMark instance from a non-VuMark database.
    """
    database = CloudDatabase()
    with MockVWS(processing_time_seconds=0.2) as mock:
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )
        target_id = vws_client.add_target(
            name="example_target",
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vumark_service = VuMarkService(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )
        with pytest.raises(
            expected_exception=InvalidTargetTypeError,
        ) as exc:
            vumark_service.generate_vumark_instance(
                target_id=target_id,
                instance_id="example_instance_id",
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
            vumark_service.generate_vumark_instance(
                target_id="exampletargetid",
                instance_id="example_instance_id",
                accept=VuMarkAccept.PNG,
            )

    assert exc.value.response.status_code == status_code
    assert failure.value in exc.value.response.text


def test_base_exception(
    *,
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """``VWSException``s has a response property."""
    with pytest.raises(expected_exception=VWSError) as exc:
        vws_client.get_target_record(target_id="a")

    assert exc.value.response.status_code == HTTPStatus.NOT_FOUND

    vws_client.add_target(
        name="x",
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )


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
            TargetStatusProcessingError,
            "https://vws.vuforia.com/targets/abc",
        ),
        (
            TargetStatusProcessingError,
            "https://example.com/prefix/targets/abc",
        ),
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
    exception_type: type[
        UnknownTargetError
        | TargetStatusProcessingError
        | TargetStatusNotSuccessError
    ],
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
