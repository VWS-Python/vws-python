"""Tests for `VWS` targets.

Test for deleting a target.
"""

from __future__ import annotations

import base64
import json
import secrets
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, BinaryIO

import pytest

from vws import VWS, CloudRecoService
from vws.reports import (
    TargetRecord,
    TargetStatuses,
)
from vws.response import Response

if TYPE_CHECKING:
    import io


class _JSONResponseTransport:
    """A transport which returns one JSON response body."""

    def __init__(self, *, body: object) -> None:
        """Create a transport for the given JSON body."""
        self._text = json.dumps(obj=body)

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
            status_code=HTTPStatus.OK,
            headers={"Content-Type": "application/json"},
            request_body=None,
            tell_position=len(content),
            content=content,
        )


@pytest.mark.parametrize(
    argnames="application_metadata",
    argvalues=[None, b"a"],
)
@pytest.mark.parametrize(argnames="active_flag", argvalues=[True, False])
def test_add_target(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
    application_metadata: bytes | None,
    cloud_reco_client: CloudRecoService,
    active_flag: bool,
) -> None:
    """No exception is raised when adding one target."""
    name = "x"
    width = 1
    if application_metadata is None:
        encoded_metadata = None
    else:
        encoded_metadata_bytes = base64.b64encode(s=application_metadata)
        encoded_metadata = encoded_metadata_bytes.decode(encoding="utf-8")

    target_id = vws_client.add_target(
        name=name,
        width=width,
        image=image,
        application_metadata=encoded_metadata,
        active_flag=active_flag,
    )
    target_record = vws_client.get_target_record(
        target_id=target_id,
    ).target_record
    assert target_record.name == name
    assert target_record.width == width
    assert target_record.active_flag is active_flag
    vws_client.wait_for_target_processed(target_id=target_id)
    matching_targets = cloud_reco_client.query(image=image)
    if active_flag:
        [matching_target] = matching_targets
        assert matching_target.target_id == target_id
        assert matching_target.target_data is not None
        query_metadata = matching_target.target_data.application_metadata
        assert query_metadata == encoded_metadata
    else:
        assert matching_targets == []


def test_add_two_targets(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """No exception is raised when adding two targets with different
    names.

    This demonstrates that the image seek position is not changed.
    """
    for name in ("a", "b"):
        _ = vws_client.add_target(
            name=name,
            width=1,
            image=image,
            active_flag=True,
            application_metadata=None,
        )


def test_list_targets(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to get a list of target IDs."""
    id_1 = vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    id_2 = vws_client.add_target(
        name="a",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    assert sorted(vws_client.list_targets()) == sorted([id_1, id_2])


def test_delete_target(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to delete a target."""
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )

    vws_client.wait_for_target_processed(target_id=target_id)
    assert vws_client.list_targets() == [target_id]
    vws_client.delete_target(target_id=target_id)
    assert vws_client.list_targets() == []


def test_get_target_record(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """Details of a target are returned by ``get_target_record``."""
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )

    result = vws_client.get_target_record(target_id=target_id)
    expected_target_record = TargetRecord(
        target_id=target_id,
        active_flag=True,
        name="x",
        width=1,
        tracking_rating=-1,
        reco_rating="",
    )

    assert result.target_record == expected_target_record

    assert result.target_record.target_id == expected_target_record.target_id
    assert (
        result.target_record.active_flag == expected_target_record.active_flag
    )
    assert result.target_record.name == expected_target_record.name
    assert result.target_record.width == expected_target_record.width
    assert (
        result.target_record.tracking_rating
        == expected_target_record.tracking_rating
    )
    assert (
        result.target_record.reco_rating == expected_target_record.reco_rating
    )

    assert result.status == TargetStatuses.PROCESSING


def test_get_failed(
    *,
    vws_client: VWS,
    image_file_failed_state: io.BytesIO,
) -> None:
    """Check that the report works with a failed target."""
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=image_file_failed_state,
        active_flag=True,
        application_metadata=None,
    )

    vws_client.wait_for_target_processed(target_id=target_id)
    result = vws_client.get_target_record(target_id=target_id)

    assert result.status == TargetStatuses.FAILED


def test_get_duplicate_targets(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to get the IDs of similar targets."""
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    similar_target_id = vws_client.add_target(
        name="a",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )

    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.wait_for_target_processed(target_id=similar_target_id)
    duplicates = vws_client.get_duplicate_targets(target_id=target_id)
    assert duplicates == [similar_target_id]


@pytest.mark.parametrize(
    argnames="similar_targets",
    argvalues=[1, ["target-id", 1]],
)
def test_invalid_duplicate_target_response(*, similar_targets: object) -> None:
    """Duplicate target IDs in responses must be a list of strings."""
    transport = _JSONResponseTransport(
        body={
            "result_code": "Success",
            "similar_targets": similar_targets,
        }
    )
    client = VWS(
        server_access_key="access-key",
        server_secret_key=secrets.token_hex(),
        transport=transport,
    )

    with pytest.raises(expected_exception=TypeError):
        _ = client.get_duplicate_targets(target_id="target-id")


@pytest.mark.parametrize(
    argnames="body",
    argvalues=[[], {"result_code": 1}],
)
def test_invalid_vws_response_envelope(*, body: object) -> None:
    """VWS responses must be objects with a string result code."""
    transport = _JSONResponseTransport(body=body)
    client = VWS(
        server_access_key="access-key",
        server_secret_key=secrets.token_hex(),
        transport=transport,
    )

    with pytest.raises(expected_exception=TypeError):
        client.delete_target(target_id="target-id")


def test_update_target(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
    different_high_quality_image: io.BytesIO,
    cloud_reco_client: CloudRecoService,
) -> None:
    """It is possible to update a target."""
    old_name = uuid.uuid4().hex
    old_width = secrets.choice(seq=range(1, 5000)) / 100
    target_id = vws_client.add_target(
        name=old_name,
        width=old_width,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    [matching_target] = cloud_reco_client.query(image=image)
    assert matching_target.target_id == target_id
    query_target_data = matching_target.target_data
    assert query_target_data is not None
    query_metadata = query_target_data.application_metadata
    assert query_metadata is None

    new_name = uuid.uuid4().hex
    new_width = secrets.choice(seq=range(1, 5000)) / 100
    new_application_metadata = base64.b64encode(s=b"a").decode(
        encoding="ascii",
    )
    vws_client.update_target(
        target_id=target_id,
        name=new_name,
        width=new_width,
        active_flag=True,
        image=different_high_quality_image,
        application_metadata=new_application_metadata,
    )

    vws_client.wait_for_target_processed(target_id=target_id)
    [
        matching_target,
    ] = cloud_reco_client.query(image=different_high_quality_image)
    assert matching_target.target_id == target_id
    query_target_data = matching_target.target_data
    assert query_target_data is not None
    query_metadata = query_target_data.application_metadata
    assert query_metadata == new_application_metadata

    vws_client.update_target(
        target_id=target_id,
        active_flag=False,
    )

    target_details = vws_client.get_target_record(target_id=target_id)
    assert target_details.target_record.name == new_name
    assert target_details.target_record.width == new_width
    assert not target_details.target_record.active_flag


def test_no_fields_given(
    *,
    vws_client: VWS,
    image: io.BytesIO | BinaryIO,
) -> None:
    """It is possible to give no update fields."""
    target_id = vws_client.add_target(
        name="x",
        width=1,
        image=image,
        active_flag=True,
        application_metadata=None,
    )
    vws_client.wait_for_target_processed(target_id=target_id)
    vws_client.update_target(target_id=target_id)
