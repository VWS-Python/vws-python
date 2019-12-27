"""
Tools for interacting with the Vuforia Cloud Recognition Web APIs.
"""

import datetime
import io
from typing import List, Optional
from urllib.parse import urljoin

import requests
from urllib3.filepost import encode_multipart_formdata
from vws_auth_tools import authorization_header, rfc_1123_date

from vws._result_codes import raise_for_result_code
from vws.exceptions import (
    ConnectionErrorPossiblyImageTooLarge,
    MatchProcessing,
    MaxNumResultsOutOfRange,
)
from vws.include_target_data import CloudRecoIncludeTargetData
from vws.reports import QueryResult, TargetData


class CloudRecoService:
    """
    An interface to the Vuforia Cloud Recognition Web APIs.
    """

    def __init__(
        self,
        client_access_key: str,
        client_secret_key: str,
        base_vwq_url: str = 'https://cloudreco.vuforia.com',
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
        image: io.BytesIO,
        max_num_results: int = 1,
        include_target_data:
        CloudRecoIncludeTargetData = CloudRecoIncludeTargetData.TOP,
    ) -> List[QueryResult]:
        """
        Use the Vuforia Web Query API to make an Image Recognition Query.

        See
        https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
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
            ~vws.exceptions.AuthenticationFailure: The client access key pair
                is not correct.
            ~vws.exceptions.MaxNumResultsOutOfRange: ``max_num_results`` is not
                within the range (1, 50).
            ~vws.exceptions.MatchProcessing: The given image matches a target
                which was recently added, updated or deleted and Vuforia
                returns an error in this case.
            ~vws.exceptions.ProjectInactive: The project is inactive.
            ~vws.exceptions.ConnectionErrorPossiblyImageTooLarge: The given
                image is too large.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
            ~vws.exceptions.BadImage: There is a problem with the given image.
                For example, it must be a JPEG or PNG file in the grayscale or
                RGB color space.

        Returns:
            An ordered list of target details of matching targets.
        """
        image_content = image.getvalue()
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'max_num_results': (None, int(max_num_results), 'text/plain'),
            'include_target_data':
            (None, include_target_data.value, 'text/plain'),
        }
        date = rfc_1123_date()
        request_path = '/v1/query'
        content, content_type_header = encode_multipart_formdata(body)
        method = 'POST'

        authorization_string = authorization_header(
            access_key=self._client_access_key,
            secret_key=self._client_secret_key,
            method=method,
            content=content,
            # Note that this is not the actual Content-Type header value sent.
            content_type='multipart/form-data',
            date=date,
            request_path=request_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': content_type_header,
        }

        try:
            response = requests.request(
                method=method,
                url=urljoin(base=self._base_vwq_url, url=request_path),
                headers=headers,
                data=content,
            )
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionErrorPossiblyImageTooLarge from exc

        if 'Integer out of range' in response.text:
            raise MaxNumResultsOutOfRange(response=response)

        if 'No content to map due to end-of-input' in response.text:
            raise MatchProcessing(response=response)

        raise_for_result_code(
            response=response,
            expected_result_code='Success',
        )

        result = []
        result_list = list(response.json()['results'])
        for item in result_list:
            target_data: Optional[TargetData] = None
            if 'target_data' in item:
                target_data_dict = item['target_data']
                metadata = target_data_dict['application_metadata']
                timestamp_string = target_data_dict['target_timestamp']
                target_timestamp = datetime.datetime.utcfromtimestamp(
                    timestamp_string,
                )
                target_data = TargetData(
                    name=target_data_dict['name'],
                    application_metadata=metadata,
                    target_timestamp=target_timestamp,
                )

            query_result = QueryResult(
                target_id=item['target_id'],
                target_data=target_data,
            )

            result.append(query_result)
        return result
