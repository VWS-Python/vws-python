"""
Tools for interacting with the Vuforia Cloud Recognition Web APIs.
"""

import datetime
import io
import json
from http import HTTPMethod, HTTPStatus
from typing import Any, BinaryIO
from urllib.parse import urljoin

import requests
from beartype import beartype
from urllib3.filepost import encode_multipart_formdata
from vws_auth_tools import authorization_header, rfc_1123_date

from vws.exceptions.cloud_reco_exceptions import (
    AuthenticationFailureError,
    BadImageError,
    InactiveProjectError,
    MaxNumResultsOutOfRangeError,
    RequestTimeTooSkewedError,
)
from vws.exceptions.custom_exceptions import (
    RequestEntityTooLargeError,
    ServerError,
)
from vws.include_target_data import CloudRecoIncludeTargetData
from vws.reports import QueryResult, TargetData
from vws.types import Response

_ImageType = io.BytesIO | BinaryIO


@beartype
def _get_image_data(image: _ImageType) -> bytes:
    """Get the data of an image file."""
    original_tell = image.tell()
    image.seek(0)
    image_data = image.read()
    image.seek(original_tell)
    return image_data


@beartype
class CloudRecoService:
    """
    An interface to the Vuforia Cloud Recognition Web APIs.
    """

    def __init__(
        self,
        client_access_key: str,
        client_secret_key: str,
        base_vwq_url: str = "https://cloudreco.vuforia.com",
    ) -> None:
        """
        Args:
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.
            base_vwq_url: The base URL for the VWQ API.
        """
        self._client_access_key = client_access_key
        self._client_secret_key = client_secret_key
        self._base_vwq_url = base_vwq_url

    def query(
        self,
        image: _ImageType,
        max_num_results: int = 1,
        include_target_data: CloudRecoIncludeTargetData = (
            CloudRecoIncludeTargetData.TOP
        ),
    ) -> list[QueryResult]:
        """
        Use the Vuforia Web Query API to make an Image Recognition Query.

        See
        https://developer.vuforia.com/library/web-api/vuforia-query-web-api
        for parameter details.

        Args:
            image: The image to make a query against.
            max_num_results: The maximum number of matching targets to be
                returned.
            include_target_data: Indicates if target_data records shall be
                returned for the matched targets. Accepted values are top
                (default value, only return target_data for top ranked match),
                none (return no target_data), all (for all matched targets).

        Raises:
            ~vws.exceptions.cloud_reco_exceptions.AuthenticationFailureError:
                The client access key pair is not correct.
            ~vws.exceptions.cloud_reco_exceptions.MaxNumResultsOutOfRangeError:
                ``max_num_results`` is not within the range (1, 50).
            ~vws.exceptions.cloud_reco_exceptions.InactiveProjectError: The
                project is inactive.
            ~vws.exceptions.cloud_reco_exceptions.RequestTimeTooSkewedError:
                There is an error with the time sent to Vuforia.
            ~vws.exceptions.cloud_reco_exceptions.BadImageError: There is a
                problem with the given image. For example, it must be a JPEG or
                PNG file in the grayscale or RGB color space.
            ~vws.exceptions.custom_exceptions.RequestEntityTooLargeError: The
                given image is too large.
            ~vws.exceptions.custom_exceptions.ServerError: There is an
                error with Vuforia's servers.

        Returns:
            An ordered list of target details of matching targets.
        """
        image_content = _get_image_data(image=image)
        body: dict[str, Any] = {
            "image": ("image.jpeg", image_content, "image/jpeg"),
            "max_num_results": (None, int(max_num_results), "text/plain"),
            "include_target_data": (
                None,
                include_target_data.value,
                "text/plain",
            ),
        }
        date = rfc_1123_date()
        request_path = "/v1/query"
        content, content_type_header = encode_multipart_formdata(fields=body)
        method = HTTPMethod.POST

        authorization_string = authorization_header(
            access_key=self._client_access_key,
            secret_key=self._client_secret_key,
            method=method,
            content=content,
            # Note that this is not the actual Content-Type header value sent.
            content_type="multipart/form-data",
            date=date,
            request_path=request_path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
            "Content-Type": content_type_header,
        }

        requests_response = requests.request(
            method=method,
            url=urljoin(base=self._base_vwq_url, url=request_path),
            headers=headers,
            data=content,
            # We should make the timeout customizable.
            timeout=30,
        )
        response = Response(
            text=requests_response.text,
            url=requests_response.url,
            status_code=requests_response.status_code,
            headers=dict(requests_response.headers),
            request_body=requests_response.request.body,
            tell_position=requests_response.raw.tell(),
        )

        if response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
            raise RequestEntityTooLargeError(response=response)

        if "Integer out of range" in response.text:
            raise MaxNumResultsOutOfRangeError(response=response)

        if (
            response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
        ):  # pragma: no cover
            raise ServerError(response=response)

        result_code = json.loads(s=response.text)["result_code"]
        if result_code != "Success":
            exception = {
                "AuthenticationFailure": AuthenticationFailureError,
                "BadImage": BadImageError,
                "InactiveProject": InactiveProjectError,
                "RequestTimeTooSkewed": RequestTimeTooSkewedError,
            }[result_code]
            raise exception(response=response)

        result: list[QueryResult] = []
        result_list = list(json.loads(s=response.text)["results"])
        for item in result_list:
            target_data: TargetData | None = None
            if "target_data" in item:
                target_data_dict = item["target_data"]
                metadata = target_data_dict["application_metadata"]
                timestamp_string = target_data_dict["target_timestamp"]
                target_timestamp = datetime.datetime.fromtimestamp(
                    timestamp=timestamp_string,
                    tz=datetime.UTC,
                )
                target_data = TargetData(
                    name=target_data_dict["name"],
                    application_metadata=metadata,
                    target_timestamp=target_timestamp,
                )

            query_result = QueryResult(
                target_id=item["target_id"],
                target_data=target_data,
            )

            result.append(query_result)
        return result
