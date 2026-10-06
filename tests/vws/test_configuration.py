"""Tests for `VWS` configuration."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, BinaryIO

import pytest
import requests
from freezegun import freeze_time
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from vws import VWS

if TYPE_CHECKING:
    import io


@pytest.mark.parametrize(
    argnames=("response_delay_seconds", "expect_timeout"),
    argvalues=[(29, False), (31, True)],
)
def test_default_timeout(
    *,
    image: io.BytesIO | BinaryIO,
    response_delay_seconds: int,
    expect_timeout: bool,
) -> None:
    """At 29 seconds there is no error; at 31 seconds there is a
    timeout.
    """
    with (
        freeze_time() as frozen_datetime,
        MockVWS(
            response_delay_seconds=response_delay_seconds,
            sleep_fn=lambda seconds: (
                frozen_datetime.tick(
                    delta=datetime.timedelta(seconds=seconds),
                ),
                None,
            )[1],
        ) as mock,
    ):
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        if expect_timeout:
            with pytest.raises(
                expected_exception=requests.exceptions.Timeout,
            ):
                _ = vws_client.add_target(
                    name="x",
                    width=1,
                    image=image,
                    active_flag=True,
                    application_metadata=None,
                )
        else:
            _ = vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )


@pytest.mark.parametrize(
    argnames=(
        "custom_timeout",
        "response_delay_seconds",
        "expect_timeout",
    ),
    argvalues=[
        (0.1, 0.09, False),
        (0.1, 0.11, True),
        ((5.0, 0.1), 0.09, False),
        ((5.0, 0.1), 0.11, True),
    ],
)
def test_custom_timeout(
    *,
    image: io.BytesIO | BinaryIO,
    custom_timeout: float | tuple[float, float],
    response_delay_seconds: float,
    expect_timeout: bool,
) -> None:
    """Custom timeouts are honored for both float and tuple forms."""
    with (
        freeze_time() as frozen_datetime,
        MockVWS(
            response_delay_seconds=response_delay_seconds,
            sleep_fn=lambda seconds: (
                frozen_datetime.tick(
                    delta=datetime.timedelta(seconds=seconds),
                ),
                None,
            )[1],
        ) as mock,
    ):
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            request_timeout_seconds=custom_timeout,
        )

        if expect_timeout:
            with pytest.raises(
                expected_exception=requests.exceptions.Timeout,
            ):
                _ = vws_client.add_target(
                    name="x",
                    width=1,
                    image=image,
                    active_flag=True,
                    application_metadata=None,
                )
        else:
            _ = vws_client.add_target(
                name="x",
                width=1,
                image=image,
                active_flag=True,
                application_metadata=None,
            )


def test_custom_base_url(image: io.BytesIO | BinaryIO) -> None:
    """
    It is possible to use add a target to a database under a custom
    VWS
    URL.
    """
    base_vws_url = "http://example.com"
    with MockVWS(base_vws_url=base_vws_url) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            base_vws_url=base_vws_url,
        )

        _ = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )


def test_custom_base_url_with_path_prefix() -> None:
    """
    A base VWS URL with a path prefix is used as-is, without the
    prefix being dropped.
    """
    base_vws_url = "http://example.com/prefix"
    with MockVWS(base_vws_url=base_vws_url) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
            base_vws_url=base_vws_url,
        )

        assert not bool(vws_client.list_targets())
