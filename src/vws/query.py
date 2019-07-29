import io
from urllib.parse import urljoin

import requests
from urllib3.filepost import encode_multipart_formdata

from ._authorization import authorization_header, rfc_1123_date


class CloudRecoService:
    """
    An interface to Vuforia Web Services APIs.
    """

    def __init__(
        self,
        client_access_key: str,
        client_secret_key: str,
        # TODO - instead use/call this vwq URL
        base_vws_url: str = 'https://cloudreco.vuforia.com',
    ) -> None:
        """
        Args:
            client_access_key: A VWS client access key.
            client_secret_key: A VWS client secret key.
            base_vws_url: The base URL for the VWS API.
        """
        self._client_access_key = client_access_key.encode()
        self._client_secret_key = client_secret_key.encode()
        self._base_vws_url = base_vws_url

    def query(
        self,
        image: io.BytesIO,
        max_num_results: int = 1,
    ) -> str:
        """
        TODO docstring
        """
        image_content = image.getvalue()
        body = {
            'image': ('image.jpeg', image_content, 'image/jpeg'),
            'max_num_results': (None, int(max_num_results), 'text/plain'),
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

        response = requests.request(
            method=method,
            url=urljoin(base=self._base_vws_url, url=request_path),
            headers=headers,
            data=content,
        )

        return response.json()['results']
        import pdb; pdb.set_trace()
        return response
