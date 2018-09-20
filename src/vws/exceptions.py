"""
Custom exceptions for Vuforia errors.
"""

from requests import Response

names = [
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

for name in names:
    globals()[name] = type(name, (Exception, ), {})
