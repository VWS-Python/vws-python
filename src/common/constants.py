"""
Constants used to make the VWS mock and wrapper.
"""

from constantly import ValueConstant, Values


class ResultCodes(Values):
    """
    Constants representing various VWS result codes.
    """
    SUCCESS = ValueConstant('Success')
    FAIL = ValueConstant('Fail')
    REQUEST_TIME_TOO_SKEWED = ValueConstant('RequestTimeTooSkewed')
