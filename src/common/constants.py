"""
Constants used to make the VWS mock and wrapper.
"""

from constantly import ValueConstant, Values


class ResultCodes(Values):
    """
    Constants representing various VWS result codes.

    See
    https://library.vuforia.com/articles/Solution/How-To-Interperete-VWS-API-Result-Codes

    Some codes here are not documented in the above link.
    """

    SUCCESS = ValueConstant('Success')
    TARGET_CREATED = ValueConstant('TargetCreated')
    AUTHENTICATION_FAILURE = ValueConstant('AuthenticationFailure')
    REQUEST_TIME_TOO_SKEWED = ValueConstant('RequestTimeTooSkewed')
    TARGET_NAME_EXIST = ValueConstant('TargetNameExist')
    UNKNOWN_TARGET = ValueConstant('UnknownTarget')
    BAD_IMAGE = ValueConstant('BadImage')
    IMAGE_TOO_LARGE = ValueConstant('ImageTooLarge')
    METADATA_TOO_LARGE = ValueConstant('MetadataTooLarge')
    DATE_RANGE_ERROR = ValueConstant('DateRangeError')
    FAIL = ValueConstant('Fail')
    TARGET_STATUS_PROCESSING = ValueConstant('TargetStatusProcessing')
    REQUEST_QUOTA_REACHED = ValueConstant('RequestQuotaReached')
    TARGET_STATUS_NOT_SUCCESS = ValueConstant('TargetStatusNotSuccess')
    PROJECT_INACTIVE = ValueConstant('ProjectInactive')


class TargetStatuses(Values):
    """
    Constants representing VWS target statuses.

    See the 'status' field in
    https://library.vuforia.com/articles/Solution/How-To-Retrieve-a-Target-Record-Using-the-VWS-API
    """

    PROCESSING = ValueConstant('processing')  # type: TargetStatuses
    SUCCESS = ValueConstant('success')  # type: TargetStatuses
    FAILED = ValueConstant('failed')  # type: TargetStatuses
