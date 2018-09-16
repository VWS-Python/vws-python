"""
Tools for interacting with Vuforia APIs.
"""

import base64
import io
import json
from enum import Enum
from time import sleep
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
import timeout_decorator
from requests import Response

from vws._authorization import authorization_header, rfc_1123_date
from vws.exceptions import (
    AuthenticationFailure,
    BadImage,
    DateRangeError,
    Fail,
    ImageTooLarge,
    InactiveProject,
    MetadataTooLarge,
    ProjectInactive,
    RequestQuotaReached,
    RequestTimeTooSkewed,
    TargetNameExist,
    TargetStatusNotSuccess,
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


class _ResultCodes(Enum):
    """
    Constants representing various VWS result codes.

    See
    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Interperete-VWS-API-Result-Codes

    Some codes here are not documented in the above link.
    """

    SUCCESS = 'Success'
    TARGET_CREATED = 'TargetCreated'
    AUTHENTICATION_FAILURE = 'AuthenticationFailure'
    REQUEST_TIME_TOO_SKEWED = 'RequestTimeTooSkewed'
    TARGET_NAME_EXIST = 'TargetNameExist'
    UNKNOWN_TARGET = 'UnknownTarget'
    BAD_IMAGE = 'BadImage'
    IMAGE_TOO_LARGE = 'ImageTooLarge'
    METADATA_TOO_LARGE = 'MetadataTooLarge'
    DATE_RANGE_ERROR = 'DateRangeError'
    FAIL = 'Fail'
    TARGET_STATUS_PROCESSING = 'TargetStatusProcessing'
    REQUEST_QUOTA_REACHED = 'RequestQuotaReached'
    TARGET_STATUS_NOT_SUCCESS = 'TargetStatusNotSuccess'
    PROJECT_INACTIVE = 'ProjectInactive'
    INACTIVE_PROJECT = 'InactiveProject'


_EXCEPTIONS = {
    _ResultCodes.AUTHENTICATION_FAILURE: AuthenticationFailure,
    _ResultCodes.REQUEST_TIME_TOO_SKEWED: RequestTimeTooSkewed,
    _ResultCodes.TARGET_NAME_EXIST: TargetNameExist,
    _ResultCodes.UNKNOWN_TARGET: UnknownTarget,
    _ResultCodes.BAD_IMAGE: BadImage,
    _ResultCodes.IMAGE_TOO_LARGE: ImageTooLarge,
    _ResultCodes.METADATA_TOO_LARGE: MetadataTooLarge,
    _ResultCodes.DATE_RANGE_ERROR: DateRangeError,
    _ResultCodes.FAIL: Fail,
    _ResultCodes.TARGET_STATUS_PROCESSING: TargetStatusProcessing,
    _ResultCodes.REQUEST_QUOTA_REACHED: RequestQuotaReached,
    _ResultCodes.TARGET_STATUS_NOT_SUCCESS: TargetStatusNotSuccess,
    _ResultCodes.PROJECT_INACTIVE: ProjectInactive,
    _ResultCodes.INACTIVE_PROJECT: InactiveProject,
}


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
        application_metadata: Optional[bytes] = None,
        active_flag: bool = True,
    ) -> str:
        """
        Add a target to a Vuforia Web Services database.

        Args:
            name: The name of the target.
            width: The width of the target.
            image: The image of the target.
            application_metadata: The application metadata of the target.
            active_flag: Whether or not the target is active for query.

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
            'application_metadata': metadata_encoded
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

        result_code = response.json()['result_code']
        if _ResultCodes(result_code) == _ResultCodes.TARGET_CREATED:
            return str(response.json()['target_id'])

        exception = _EXCEPTIONS[_ResultCodes(result_code)]
        raise exception(response=response)

    def get_target(self, target_id: str) -> Dict[str, Any]:
        """
        Get details of a given target.

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

        result_code = response.json()['result_code']
        if _ResultCodes(result_code) == _ResultCodes.SUCCESS:
            return dict(response.json())

        exception = _EXCEPTIONS[_ResultCodes(result_code)]
        raise exception(response=response)

    def delete_target(self, target_id: str) -> None:
        """
        Delete a given target.

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

        result_code = response.json()['result_code']
        if _ResultCodes(result_code) == _ResultCodes.SUCCESS:
            return

        exception = _EXCEPTIONS[_ResultCodes(result_code)]
        raise exception(response=response)

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

        return list(response.json()['results'])

    def get_target_summary_report(
        self,
        target_id: str,
    ) -> Dict[str, Union[str, int]]:
        """
        Get a summary report for a target.

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

        result_code = response.json()['result_code']
        if _ResultCodes(result_code) == _ResultCodes.SUCCESS:
            return dict(response.json())

        exception = _EXCEPTIONS[_ResultCodes(result_code)]
        raise exception(response=response)

    def get_database_summary(self) -> Dict[str, Union[str, int]]:
        """
        Get a summary of a database.

        Args:
            target_id: The ID of the target to wait for.

        Returns:
            The IDs of all targets in the database.
        """
        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method='GET',
            content=b'',
            request_path='/summary',
            base_vws_url=self._base_vws_url,
        )

        return dict(response.json())
