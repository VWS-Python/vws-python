"""
Tests for exceptions raised when using the CloudRecoService.
"""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase
from mock_vws.states import States
from vws import CloudRecoService
from vws.exceptions.base_exceptions import CloudRecoException
from vws.exceptions.cloud_reco_exceptions import (
    AuthenticationFailure,
    BadImage,
    InactiveProject,
    MaxNumResultsOutOfRange,
    RequestTimeTooSkewed,
)
from vws.exceptions.custom_exceptions import (
    RequestEntityTooLarge,
)

if TYPE_CHECKING:
    import io


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
        "Accepted range is from 1 to 50 (inclusive)."
    )
    assert str(exc.value) == exc.value.response.text == expected_value


def test_image_too_large(
    cloud_reco_client: CloudRecoService,
    png_too_large: io.BytesIO,
) -> None:
    """
    A ``RequestEntityTooLarge`` exception is raised if an image which is too
    large is given.
    """
    with pytest.raises(RequestEntityTooLarge):
        cloud_reco_client.query(image=png_too_large)


def test_cloudrecoexception_inheritance() -> None:
    """
    CloudRecoService-specific exceptions inherit from CloudRecoException.
    """
    subclasses = [
        MaxNumResultsOutOfRange,
        InactiveProject,
        BadImage,
        AuthenticationFailure,
        RequestTimeTooSkewed,
    ]
    for subclass in subclasses:
        assert issubclass(subclass, CloudRecoException)


def test_authentication_failure(high_quality_image: io.BytesIO) -> None:
    """
    An ``AuthenticationFailure`` exception is raised when the client access key
    exists but the client secret key is incorrect.
    """
    database = VuforiaDatabase()
    cloud_reco_client = CloudRecoService(
        client_access_key=database.client_access_key,
        client_secret_key=uuid.uuid4().hex,
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
