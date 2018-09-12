import io
from typing import Union
import json
import requests
import base64
from urllib.parse import urljoin

from ._authorization import rfc_1123_date, authorization_header
from .exceptions import VWSException

class ResultCodes(Enum):
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



class VWS:
    def __init__(self, server_access_key: str, server_secret_key: str) -> None:
        self.server_access_key = server_access_key.encode()
        self.server_secret_key = server_secret_key.encode()

    def add_target(
        self,
        name: str,
        width: Union[int, float],
        image: io.BytesIO,
    ) -> str:
        image_data = image.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': name,
            'width': width,
            'image': image_data_encoded,
        }

        date = rfc_1123_date()
        request_path = '/targets'
        content_type = 'application/json'
        method = 'POST'

        content = bytes(json.dumps(data), encoding='utf-8')

        authorization_string = authorization_header(
            access_key=self.server_access_key,
            secret_key=self.server_secret_key,
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
            url=urljoin(base='https://vws.vuforia.com/', url=request_path),
            headers=headers,
            data=content,
        )

        if response.status_code == requests.codes.CREATED:
            return 'a'

        result_code = response.json()['result_code']
        exceptions = {
            AUTHENTICATION_FAILURE: AuthenticationFailure,
            REQUEST_TIME_TOO_SKEWED: RequestTimeTooSkewed,
            TARGET_NAME_EXIST: TargetNameExist,
            UNKNOWN_TARGET: UnknownTarget,
            BAD_IMAGE: BadImage,
            IMAGE_TOO_LARGE: ImageTooLarge,
            METADATA_TOO_LARGE: MetadataTooLarge,
            DATE_RANGE_ERROR: DateRangeError,
            FAIL: Fail,
            TARGET_STATUS_PROCESSING: TargetStatusProcessing,
            REQUEST_QUOTA_REACHED: RequestQuotaReached,
            TARGET_STATUS_NOT_SUCCESS: TargetStatusNotSuccess,
            PROJECT_INACTIVE: ProjectInactive,
            INACTIVE_PROJECT: InactiveProject,
        }

        raise VWSException(response=response)
