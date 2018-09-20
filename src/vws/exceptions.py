"""
Custom exceptions for Vuforia errors.
"""

from requests import Response

_NAMES = [
    'Success',
    'TargetCreated',
    'AuthenticationFailure',
    'RequestTimeTooSkewed',
    'TargetNameExist',
    'UnknownTarget',
    'BadImage',
    'ImageTooLarge',
    'MetadataTooLarge',
    'DateRangeError',
    'Fail',
    'TargetStatusProcessing',
    'RequestQuotaReached',
    'TargetStatusNotSuccess',
    'ProjectInactive',
    'InactiveProject',
]

_DOC_TEMPLATE = (
    'Exception raised when Vuforia returns a response with a result code'
    "'{name}'."
)


def _INIT(self, response: Response):
    self.response = response


for _NAME in _NAMES:
    _ATTRIBUTE_DICT = {
        '__doc__': _DOC_TEMPLATE.format(name=_NAME),
        '__init__': _INIT,
    }
    globals()[_NAME] = type(_NAME, (Exception, ), _ATTRIBUTE_DICT)
