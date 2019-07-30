"""
Tools for interacting with the Vuforia Cloud Recognition Web APIs.
"""

import io
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from urllib3.filepost import encode_multipart_formdata

from ._authorization import authorization_header, rfc_1123_date


class CloudRecoService:
    """
    An interface to the Vuforia Cloud Recognition Web APIs.
    """

    def __init__(
        self,
        client_access_key: str,
        client_secret_key: str,
    ) -> None:
        """
        Args:
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.
        """
        self._client_access_key = client_access_key.encode()
        self._client_secret_key = client_secret_key.encode()

    def query(self, image: io.BytesIO) -> List[Dict[str, Any]]:
        """
        Use the Vuforia Web Query API to make an Image Recognition Query.

        See
        https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query
        for parameter details.

        Args:
            image: The image to make a query against.

        Returns:
            An ordered list of target details of matching targets.
        """
        image_content = image.getvalue()
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
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

        base_vwq_url = 'https://cloudreco.vuforia.com'
        response = requests.request(
            method=method,
            url=urljoin(base=base_vwq_url, url=request_path),
            headers=headers,
            data=content,
        )

        return list(response.json()['results'])
