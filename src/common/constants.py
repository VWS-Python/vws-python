"""
Constants used to make the VWS mock and wrapper.
"""

from constantly import ValueConstant, Values


class ResultCodes(Values):
    """
    Constants representing various VWS result codes.

    See
    https://library.vuforia.com/articles/Solution/How-To-Interperete-VWS-API-Result-Codes
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
