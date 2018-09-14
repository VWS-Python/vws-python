"""
Tools for interacting with Vuforia APIs.
"""

import base64
import io
import json
from enum import Enum
from typing import Optional, Union
from urllib.parse import urljoin

import requests

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


_exceptions = {
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
    ) -> str:
        """
        Add a target to a Vuforia Web Services database.

        Args:
            name: The name of the target.
            width: The width of the target.
            image: The image of the target.
            application_metadata: The application metadata of the target.
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
            'application_metadata': metadata_encoded,
        }

        date = rfc_1123_date()
        request_path = '/targets'
        content_type = 'application/json'
        method = 'POST'

        content = bytes(json.dumps(data), encoding='utf-8')

        authorization_string = authorization_header(
            access_key=self._server_access_key,
            secret_key=self._server_secret_key,
            method=method,
            content=content,
            content_type=content_type,
            date=date,
            request_path=request_path,
        )

        headers = {
            'Authorization': authorization_string,
            'Date': date,
            'Content-Type': content_type,
        }

        response = requests.request(
            method=method,
            url=urljoin(base=self._base_vws_url, url=request_path),
            headers=headers,
            data=content,
        )

        if response.status_code == requests.codes.CREATED:
            return 'a'

        result_code = response.json()['result_code']
        exception = _exceptions[_ResultCodes(result_code)]
        raise exception(response=response)
