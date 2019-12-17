"""
Tests for various exceptions.
"""

import io

import pytest
from freezegun import freeze_time
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from mock_vws.states import States
from requests import codes

from vws import VWS, CloudRecoService
from vws.exceptions import (
    AuthenticationFailure,
    BadImage,
    Fail,
    ImageTooLarge,
    MatchProcessing,
    MetadataTooLarge,
    ProjectInactive,
    RequestTimeTooSkewed,
    TargetNameExist,
    TargetStatusNotSuccess,
    TargetStatusProcessing,
    UnknownTarget,
    UnknownVWSErrorPossiblyBadName,
)


def test_image_too_large(
    vws_client: VWS,
    png_too_large: io.BytesIO,
) -> None:
    """
    When giving an image which is too large, an ``ImageTooLarge`` exception is
    raised.
    """
    with pytest.raises(ImageTooLarge) as exc:
        vws_client.add_target(
            name='x',
            width=1,
            image=png_too_large,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == codes.UNPROCESSABLE_ENTITY


def test_invalid_given_id(vws_client: VWS) -> None:
    """
    Giving an invalid ID to a helper which requires a target ID to be given
    causes an ``UnknownTarget`` exception to be raised.
    """
    target_id = '12345abc'
    with pytest.raises(UnknownTarget) as exc:
        vws_client.delete_target(target_id=target_id)
    assert exc.value.response.status_code == codes.NOT_FOUND
    assert exc.value.target_id == target_id


def test_add_bad_name(vws_client: VWS, high_quality_image: io.BytesIO) -> None:
    """
    When a name with a bad character is given, an
    ``UnknownVWSErrorPossiblyBadName`` exception is raised.
    """
    max_char_value = 65535
    bad_name = chr(max_char_value + 1)
    with pytest.raises(UnknownVWSErrorPossiblyBadName):
        vws_client.add_target(
            name=bad_name,
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )


def test_request_quota_reached() -> None:
    """
    See https://github.com/adamtheturtle/vws-python/issues/822 for writing
    this test.
    """


def test_fail(high_quality_image: io.BytesIO) -> None:
    """
    A ``Fail`` exception is raised when the server access key does not exist.
    """
    with MockVWS():
        vws_client = VWS(
            server_access_key='a',
            server_secret_key='a',
        )

        with pytest.raises(Fail) as exc:
            vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == codes.BAD_REQUEST


def test_bad_image(vws_client: VWS) -> None:
    """
    A ``BadImage`` exception is raised when a non-image is given.
    """
    not_an_image = io.BytesIO(b'Not an image')
    with pytest.raises(BadImage) as exc:
        vws_client.add_target(
            name='x',
            width=1,
            image=not_an_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == codes.UNPROCESSABLE_ENTITY


def test_target_name_exist(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetNameExist`` exception is raised after adding two targets with
    the same name.
    """
    vws_client.add_target(
        name='x',
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )
    with pytest.raises(TargetNameExist) as exc:
        vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

    assert exc.value.response.status_code == codes.FORBIDDEN
    assert exc.value.target_name == 'x'


def test_project_inactive(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``ProjectInactive`` exception is raised if adding a target to an
    inactive database.
    """
    database = VuforiaDatabase(state=States.PROJECT_INACTIVE)
    with MockVWS() as mock:
        mock.add_database(database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
        )

        with pytest.raises(ProjectInactive) as exc:
            vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == codes.FORBIDDEN

        with pytest.raises(ProjectInactive) as exc:
            cloud_reco_client.query(image=high_quality_image)

        assert exc.value.response.status_code == codes.FORBIDDEN


def test_target_status_processing(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetStatusProcessing`` exception is raised if trying to delete a
    target which is processing.
    """
    target_id = vws_client.add_target(
        name='x',
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )

    with pytest.raises(TargetStatusProcessing) as exc:
        vws_client.delete_target(target_id=target_id)

    assert exc.value.response.status_code == codes.FORBIDDEN
    assert exc.value.target_id == target_id


def test_metadata_too_large(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``MetadataTooLarge`` exception is raised if the metadata given is too
    large.
    """
    with pytest.raises(MetadataTooLarge) as exc:
        vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata='a' * 1024 * 1024 * 10,
        )

    assert exc.value.response.status_code == codes.UNPROCESSABLE_ENTITY


def test_request_time_too_skewed(vws_client: VWS) -> None:
    """
    A ``RequestTimeTooSkewed`` exception is raised when the request time is
    more than five minutes different from the server time.
    """
    vws_max_time_skew = 60 * 5
    leeway = 10
    time_difference_from_now = vws_max_time_skew + leeway

    # We use a custom tick because we expect the following:
    #
    # * At least one time check when creating the request
    # * At least one time check when processing the request
    #
    # >= 1 ticks are acceptable.
    with freeze_time(auto_tick_seconds=time_difference_from_now):
        with pytest.raises(RequestTimeTooSkewed) as exc:
            vws_client.get_target_record(target_id='a')

    assert exc.value.response.status_code == codes.FORBIDDEN


def test_authentication_failure(high_quality_image: io.BytesIO) -> None:
    """
    An ``AuthenticationFailure`` exception is raised when the server access key
    exists but the server secret key is incorrect, or when a client key is
    incorrect.
    """
    database = VuforiaDatabase()
    with MockVWS() as mock:
        mock.add_database(database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key='a',
        )

        with pytest.raises(AuthenticationFailure) as exc:
            vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

        assert exc.value.response.status_code == codes.UNAUTHORIZED

        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key='a',
        )

        with pytest.raises(AuthenticationFailure) as exc:
            cloud_reco_client.query(image=high_quality_image)

        assert exc.value.response.status_code == codes.UNAUTHORIZED


def test_target_status_not_success(
    vws_client: VWS,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``TargetStatusNotSuccess`` exception is raised when updating a target
    which has a status which is not "Success".
    """
    target_id = vws_client.add_target(
        name='x',
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )

    with pytest.raises(TargetStatusNotSuccess) as exc:
        vws_client.update_target(target_id=target_id)

    assert exc.value.response.status_code == codes.FORBIDDEN
    assert exc.value.target_id == target_id


def test_match_processing(
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``MatchProcessing`` exception is raised when a target in processing is
    matched.
    """
    vws_client.add_target(
        name='x',
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )
    with pytest.raises(MatchProcessing) as exc:
        cloud_reco_client.query(image=high_quality_image)
    assert exc.value.response.status_code == codes.INTERNAL_SERVER_ERROR
