"""
Tests for exceptions raised when using the CloudRecoService.
"""

import io
from http import HTTPStatus

import pytest
import requests
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from mock_vws.states import States

from vws import VWS, CloudRecoService
from vws.exceptions.base_exceptions import CloudRecoException
from vws.exceptions.cloud_reco_exceptions import (
    AuthenticationFailure,
    InactiveProject,
    MatchProcessing,
    MaxNumResultsOutOfRange,
)
from vws.exceptions.custom_exceptions import (
    ConnectionErrorPossiblyImageTooLarge,
)


def test_too_many_max_results(
    cloud_reco_client: CloudRecoService,
    high_quality_image: io.BytesIO,
) -> None:
    """
    A ``MaxNumResultsOutOfRange`` error is raised if the given
    ``max_num_results`` is out of range.
    """
    with pytest.raises(MaxNumResultsOutOfRange) as exc:
        cloud_reco_client.query(
            image=high_quality_image,
            max_num_results=51,
        )

    expected_value = (
        "Integer out of range (51) in form data part 'max_result'. "
        'Accepted range is from 1 to 50 (inclusive).'
    )
    assert str(exc.value) == exc.value.response.text == expected_value


def test_image_too_large(
    cloud_reco_client: CloudRecoService,
    png_too_large: io.BytesIO,
) -> None:
    """
    A ``ConnectionErrorPossiblyImageTooLarge`` exception is raised if an
    image which is too large is given.
    """
    with pytest.raises(ConnectionErrorPossiblyImageTooLarge) as exc:
        cloud_reco_client.query(image=png_too_large)

    assert isinstance(exc.value, requests.ConnectionError)


def test_cloudrecoexception_inheritance() -> None:
    """
    CloudRecoService-specific exceptions inherit from CloudRecoException.
    """
    subclasses = [
        MatchProcessing,
        MaxNumResultsOutOfRange,
    ]
    for subclass in subclasses:
        assert issubclass(subclass, CloudRecoException)


def test_base_exception(
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    high_quality_image: io.BytesIO,
) -> None:
    """
    ``CloudRecoException``s has a response property.
    """
    vws_client.add_target(
        name='x',
        width=1,
        image=high_quality_image,
        active_flag=True,
        application_metadata=None,
    )

    with pytest.raises(CloudRecoException) as exc:
        cloud_reco_client.query(image=high_quality_image)

    assert exc.value.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


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
    assert exc.value.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


def test_authentication_failure(high_quality_image: io.BytesIO) -> None:
    """
    An ``AuthenticationFailure`` exception is raised when the client access key
    exists but the client secret key is incorrect.
    """
    database = VuforiaDatabase()
    cloud_reco_client = CloudRecoService(
        client_access_key=database.client_access_key,
        client_secret_key='a',
    )
    with MockVWS() as mock:
        mock.add_database(database=database)

        with pytest.raises(AuthenticationFailure) as exc:
            cloud_reco_client.query(image=high_quality_image)

        assert exc.value.response.status_code == HTTPStatus.UNAUTHORIZED


def test_inactive_project(high_quality_image: io.BytesIO) -> None:
    """
    An ``InactiveProject`` exception is raised when querying an inactive
    database.
    """
    database = VuforiaDatabase(state=States.PROJECT_INACTIVE)
    with MockVWS() as mock:
        mock.add_database(database=database)
        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
        )

        with pytest.raises(InactiveProject) as exc:
            cloud_reco_client.query(image=high_quality_image)

        assert exc.value.response.status_code == HTTPStatus.FORBIDDEN
