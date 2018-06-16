"""
Constants used to make the VWS mock.
"""

from enum import Enum, auto


class States(Enum):
    """
    Constants representing various web service states.
    """

    WORKING = auto()

    # A project is inactive if the license key has been deleted.
    PROJECT_INACTIVE = auto()

    def __repr__(self) -> str:
        """
        Return a representation which does not include the generated number.
        """
        return '<{class_name}.{state_name}>'.format(
            class_name=self.__class__.__name__,
            state_name=self.name,
        )


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


class TargetStatuses(Enum):
    """
    Constants representing VWS target statuses.

    See the 'status' field in
    https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Retrieve-a-Target-Record
    """

    PROCESSING = 'processing'
    SUCCESS = 'success'
    FAILED = 'failed'
