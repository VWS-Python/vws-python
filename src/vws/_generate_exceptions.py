"""
Script which generates part of ``exceptions.py``.
"""

from enum import Enum
from textwrap import dedent


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


template = dedent(
    """
    class {name}(Exception):
        def __init__(self, response: Response) -> None:
            \"\"\"
            Exception raised when Vuforia returns a response with a result code
            '{name}'.
            \"\"\"
            self.response = response
    """,
)

success_codes = {_ResultCodes.SUCCESS, _ResultCodes.TARGET_CREATED}
for result_code in set(_ResultCodes) - success_codes:
    print(template.format(name=result_code.value))
