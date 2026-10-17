"""Tests for the ``CloudRecoService`` querying functionality."""

from __future__ import annotations

import datetime as dt
import json
import secrets
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, BinaryIO, Literal

import pytest
import requests
from freezegun import freeze_time
from mock_vws import MockVWS
from mock_vws.database import CloudDatabase

from tests.image_factory import IMAGE_CASES, ImageFactory
from vws import VWS, CloudRecoService
from vws.exceptions.custom_exceptions import ServerError
from vws.include_target_data import CloudRecoIncludeTargetData
from vws.response import Response

if TYPE_CHECKING:
    import io


class _JSONResponseTransport:
    """A transport which returns one JSON response body."""

    def __init__(
        self,
        *,
        body: object,
        status_code: HTTPStatus,
    ) -> None:
        """Create a transport for the given JSON body."""
        self._text = json.dumps(obj=body)
        self._status_code = status_code

    def close(self) -> None:
        """Close the transport."""

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes,
        request_timeout: float | tuple[float, float],
    ) -> Response:
        """Return the configured response body."""
        del method, headers, data, request_timeout
        content = self._text.encode()
        return Response(
            text=self._text,
            url=url,
            status_code=self._status_code,
            headers={"Content-Type": "application/json"},
            request_body=None,
            tell_position=len(content),
            content=content,
        )


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_no_matches(
    *,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """An empty list is returned if there are no matches."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    result = cloud_reco_client.query(image=image)
    assert result == []


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_match(
    *,
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """Details of matching targets are returned."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    [matching_target] = cloud_reco_client.query(image=image)
    assert matching_target.target_id == target_id


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_invalid_results(
    *,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """Query results in responses must be a list of objects."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    transport = _JSONResponseTransport(
        body={"result_code": "Success", "results": 1},
        status_code=HTTPStatus.OK,
    )
    client = CloudRecoService(
        client_access_key="access-key",
        client_secret_key=secrets.token_hex(),
        transport=transport,
    )

    with pytest.raises(expected_exception=TypeError):
        _ = client.query(image=image)


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_server_error(
    *,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """Server errors are exposed through the public query client."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    transport = _JSONResponseTransport(
        body={},
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    client = CloudRecoService(
        client_access_key="access-key",
        client_secret_key=secrets.token_hex(),
        transport=transport,
    )

    with pytest.raises(expected_exception=ServerError):
        _ = client.query(image=image)


@pytest.mark.parametrize(
    argnames=("response_delay_seconds", "expect_timeout"),
    argvalues=[(29, False), (31, True)],
)
@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_default_timeout(
    *,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
    response_delay_seconds: int,
    expect_timeout: bool,
) -> None:
    """At 29 seconds there is no error; at 31 seconds there is a
    timeout.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    with (
        freeze_time() as frozen_datetime,
        MockVWS(
            response_delay_seconds=response_delay_seconds,
            sleep_fn=lambda seconds: (
                frozen_datetime.tick(
                    delta=dt.timedelta(seconds=seconds),
                ),
                None,
            )[1],
        ) as mock,
    ):
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
        )

        if expect_timeout:
            with pytest.raises(
                expected_exception=requests.exceptions.Timeout,
            ):
                _ = cloud_reco_client.query(image=image)
        else:
            matches = cloud_reco_client.query(image=image)
            assert not bool(matches)


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
@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_custom_timeout(
    *,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
    custom_timeout: float | tuple[float, float],
    response_delay_seconds: float,
    expect_timeout: bool,
) -> None:
    """Custom timeouts are honored for both float and tuple forms."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    with (
        freeze_time() as frozen_datetime,
        MockVWS(
            response_delay_seconds=response_delay_seconds,
            sleep_fn=lambda seconds: (
                frozen_datetime.tick(
                    delta=dt.timedelta(seconds=seconds),
                ),
                None,
            )[1],
        ) as mock,
    ):
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
            request_timeout_seconds=custom_timeout,
        )

        if expect_timeout:
            with pytest.raises(
                expected_exception=requests.exceptions.Timeout,
            ):
                _ = cloud_reco_client.query(image=image)
        else:
            matches = cloud_reco_client.query(image=image)
            assert not bool(matches)


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_custom_base_url(
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """
    It is possible to use query a target to a database under a
    custom
    VWQ
    URL.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    base_vwq_url = "http://example.com"
    with MockVWS(base_vwq_url=base_vwq_url) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )

        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )

        vws_client.wait_for_target_processed(target_id=target_id)

        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
            base_vwq_url=base_vwq_url,
        )

        matches = cloud_reco_client.query(image=image)
        assert len(matches) == 1
        match = matches[0]
        assert match.target_id == target_id


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_custom_base_url_with_path_prefix(
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """
    A base VWQ URL with a path prefix is used as-is, without the
    prefix being dropped.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    base_vwq_url = "http://example.com/prefix"
    with MockVWS(base_vwq_url=base_vwq_url) as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )
        target_id = vws_client.add_target(
            name="x",
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
            base_vwq_url=base_vwq_url,
        )

        matches = cloud_reco_client.query(image=image)
        assert len(matches) == 1


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_max_num_results_default(
    *,
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """By default the maximum number of results is 1."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    target_id_2 = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.wait_for_target_processed(target_id=target_id_2)
    matches = cloud_reco_client.query(image=image)
    assert len(matches) == 1


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_custom(
    *,
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """It is possible to set a custom ``max_num_results``."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    target_id_2 = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    target_id_3 = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.wait_for_target_processed(target_id=target_id_2)
    vws_client.wait_for_target_processed(target_id=target_id_3)
    max_num_results = 2
    matches = cloud_reco_client.query(
        image=image,
        max_num_results=max_num_results,
    )
    assert len(matches) == max_num_results


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_include_target_data_default(
    *,
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """By default, target data is only returned in the top match."""
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    target_id_2 = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.wait_for_target_processed(target_id=target_id_2)
    top_match, second_match = cloud_reco_client.query(
        image=image,
        max_num_results=2,
    )
    assert top_match.target_data is not None
    assert second_match.target_data is None


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_top(
    *,
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """
    When ``CloudRecoIncludeTargetData.TOP`` is given, target data is
    only
    returned in the top match.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    target_id_2 = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.wait_for_target_processed(target_id=target_id_2)
    top_match, second_match = cloud_reco_client.query(
        image=image,
        max_num_results=2,
        include_target_data=CloudRecoIncludeTargetData.TOP,
    )
    assert top_match.target_data is not None
    assert second_match.target_data is None


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_none(
    *,
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """
    When ``CloudRecoIncludeTargetData.NONE`` is given, target data
    is
    not
    returned in any match.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    target_id_2 = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.wait_for_target_processed(target_id=target_id_2)
    top_match, second_match = cloud_reco_client.query(
        image=image,
        max_num_results=2,
        include_target_data=CloudRecoIncludeTargetData.NONE,
    )
    assert top_match.target_data is None
    assert second_match.target_data is None


@pytest.mark.parametrize(
    argnames=("image_source", "image_mode"), argvalues=IMAGE_CASES
)
def test_all(
    *,
    vws_client: VWS,
    cloud_reco_client: CloudRecoService,
    image_factory: ImageFactory,
    image_source: Literal["high_quality_image", "image_file"],
    image_mode: Literal["r+b", "rb"],
) -> None:
    """
    When ``CloudRecoIncludeTargetData.ALL`` is given, target data is
    returned in all matches.
    """
    image: io.BytesIO | BinaryIO = image_factory.create(
        source=image_source, mode=image_mode
    )
    target_id = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    target_id_2 = vws_client.add_target(
        name=uuid.uuid4().hex,
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.wait_for_target_processed(target_id=target_id_2)
    top_match, second_match = cloud_reco_client.query(
        image=image,
        max_num_results=2,
        include_target_data=CloudRecoIncludeTargetData.ALL,
    )
    assert top_match.target_data is not None
    assert second_match.target_data is not None
