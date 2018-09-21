"""
Tools for interacting with Vuforia APIs.
"""

import base64
import io
import json
from enum import Enum
from time import sleep
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
import timeout_decorator
from requests import Response

from vws._authorization import authorization_header, rfc_1123_date
from vws.exceptions import (
    ImageTooLarge,
    MetadataTooLarge,
    TargetNameExist,
    TargetStatusProcessing,
    UnknownTarget,
)


def _target_api_request(
    server_access_key: bytes,
    server_secret_key: bytes,
    method: str,
    content: bytes,
    request_path: str,
    base_vws_url: str,
) -> Response:
    """
    Make a request to the Vuforia Target API.

    This uses `requests` to make a request against https://vws.vuforia.com.
    The content type of the request will be `application/json`.

    Args:
        server_access_key: A VWS server access key.
        server_secret_key: A VWS server secret key.
        method: The HTTP method which will be used in the request.
        content: The request body which will be used in the request.
        request_path: The path to the endpoint which will be used in the
            request.

        base_vws_url: The base URL for the VWS API.

    Returns:
        The response to the request made by `requests`.
    """
    date = rfc_1123_date()
    content_type = 'application/json'

    signature_string = authorization_header(
        access_key=server_access_key,
        secret_key=server_secret_key,
        method=method,
        content=content,
        content_type=content_type,
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': signature_string,
        'Date': date,
        'Content-Type': content_type,
    }

    url = urljoin(base=base_vws_url, url=request_path)

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        data=content,
    )

    return response


def _raise_for_result_code(
    response: Response,
    expected_result_code: str,
) -> None:
    """
    Raise an appropriate exception if the expected result code for a successful
    request is not returned.
    """
    result_code = response.json()['result_code']
    if result_code == expected_result_code:
        return

    exception = {
        'ImageTooLarge': ImageTooLarge,
        'MetadataTooLarge': MetadataTooLarge,
        'TargetNameExist': TargetNameExist,
        'TargetStatusProcessing': TargetStatusProcessing,
        'UnknownTarget': UnknownTarget,
    }[result_code]

    raise exception(response=response)


class VWS:
    """
    An interface to Vuforia Web Services APIs.
    """

    def __init__(
        self,
        server_access_key: str,
        server_secret_key: str,
        base_vws_url: str = 'https://vws.vuforia.com',
    ) -> None:
        """
        Args:
            server_access_key: A VWS server access key.
            server_secret_key: A VWS server secret key.
            base_vws_url: The base URL for the VWS API.
        """
        self._server_access_key = server_access_key.encode()
        self._server_secret_key = server_secret_key.encode()
        self._base_vws_url = base_vws_url

    def add_target(
        self,
        name: str,
        width: Union[int, float],
        image: io.BytesIO,
        active_flag: bool = True,
        application_metadata: Optional[bytes] = None,
    ) -> str:
        """
        Add a target to a Vuforia Web Services database.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Add-a-Target.

        Args:
            name: The name of the target.
            width: The width of the target.
            image: The image of the target.
            active_flag: Whether or not the target is active for query.
            application_metadata: The application metadata of the target.
                This will be base64 encoded.

        Returns:
            The target ID of the new target.
        """
        image_data = image.getvalue()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')
        if application_metadata is None:
            metadata_encoded = None
        else:
            metadata_encoded_str = base64.b64encode(application_metadata)
            metadata_encoded = metadata_encoded_str.decode('ascii')

        data = {
            'name': name,
            'width': width,
            'image': image_data_encoded,
            'active_flag': active_flag,
            'application_metadata': metadata_encoded,
        }

        content = bytes(json.dumps(data), encoding='utf-8')

        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method='POST',
            content=content,
            request_path='/targets',
            base_vws_url=self._base_vws_url,
        )

        _raise_for_result_code(
            response=response,
            expected_result_code='TargetCreated',
        )

        return str(response.json()['target_id'])

    def get_target_record(self, target_id: str) -> Dict[str, Union[str, int]]:
        """
        Get a given target's target record from the Target Management System.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Retrieve-a-Target-Record.

        Args:
            target_id: The ID of the target to get details of.

        Returns:
            Response details of a target from Vuforia.
        """
        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method='GET',
            content=b'',
            request_path=f'/targets/{target_id}',
            base_vws_url=self._base_vws_url,
        )

        _raise_for_result_code(
            response=response,
            expected_result_code='Success',
        )
        return dict(response.json()['target_record'])

    @timeout_decorator.timeout(seconds=60 * 5)
    def wait_for_target_processed(self, target_id: str) -> None:
        """
        Wait up to five minutes (arbitrary) for a target to get past the
        processing stage.

        Args:
            target_id: The ID of the target to wait for.

        Raises:
            TimeoutError: The target remained in the processing stage for more
                than five minutes.
        """
        while True:
            report = self.get_target_summary_report(target_id=target_id)
            if report['status'] != 'processing':
                return

            # We wait 0.2 seconds rather than less than that to decrease the
            # number of calls made to the API, to decrease the likelihood of
            # hitting the request quota.
            sleep(0.2)

    def list_targets(self) -> List[str]:
        """
        List target IDs.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Get-a-Target-List-for-a-Cloud-Database.

        Returns:
            The IDs of all targets in the database.
        """
        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method='GET',
            content=b'',
            request_path='/targets',
            base_vws_url=self._base_vws_url,
        )

        _raise_for_result_code(
            response=response,
            expected_result_code='Success',
        )
        return list(response.json()['results'])

    def get_target_summary_report(
        self,
        target_id: str,
    ) -> Dict[str, Union[str, int]]:
        """
        Get a summary report for a target.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Retrieve-a-Target-Summary-Report.

        Args:
            target_id: The ID of the target to get a summary report for.

        Returns:
            Details of the target.
        """
        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method='GET',
            content=b'',
            request_path=f'/summary/{target_id}',
            base_vws_url=self._base_vws_url,
        )

        _raise_for_result_code(
            response=response,
            expected_result_code='Success',
        )
        return dict(response.json())

    def get_database_summary_report(self) -> Dict[str, Union[str, int]]:
        """
        Get a summary report for the database.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Get-a-Database-Summary-Report.

        Returns:
            Details of the database.
        """
        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method='GET',
            content=b'',
            request_path='/summary',
            base_vws_url=self._base_vws_url,
        )

        _raise_for_result_code(
            response=response,
            expected_result_code='Success',
        )

        return dict(response.json())

    def delete_target(self, target_id: str) -> None:
        """
        Delete a given target.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Delete-a-Target.

        Args:
            target_id: The ID of the target to delete.
        """
        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method='DELETE',
            content=b'',
            request_path=f'/targets/{target_id}',
            base_vws_url=self._base_vws_url,
        )

        _raise_for_result_code(
            response=response,
            expected_result_code='Success',
        )
