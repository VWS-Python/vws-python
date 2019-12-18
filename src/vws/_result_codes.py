"""
Tools for managing result codes.
"""

import json

from requests import Response

from vws.exceptions import (
    AuthenticationFailure,
    BadImage,
    DateRangeError,
    Fail,
    ImageTooLarge,
    MetadataTooLarge,
    ProjectHasNoAPIAccess,
    ProjectInactive,
    ProjectSuspended,
    RequestQuotaReached,
    RequestTimeTooSkewed,
    TargetNameExist,
    TargetQuotaReached,
    TargetStatusNotSuccess,
    TargetStatusProcessing,
    UnknownTarget,
    UnknownVWSErrorPossiblyBadName,
)


def raise_for_result_code(
    response: Response,
    expected_result_code: str,
) -> None:
    """
    Raise an appropriate exception if the expected result code for a successful
    request is not returned.

    Args:
        response: A response from Vuforia.
        expected_result_code: See
            https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Interperete-VWS-API-Result-Codes

    Raises:
        ~vws.exceptions.UnknownVWSErrorPossiblyBadName: Vuforia returns an HTML
            page with the text "Oops, an error occurred". This has been seen to
            happen when the given name includes a bad character.
    """
    try:
        result_code = response.json()['result_code']
    except json.decoder.JSONDecodeError as exc:
        assert 'Oops' in response.text
        raise UnknownVWSErrorPossiblyBadName() from exc

    if result_code == expected_result_code:
        return

    exception = {
        'AuthenticationFailure': AuthenticationFailure,
        'BadImage': BadImage,
        'DateRangeError': DateRangeError,
        'Fail': Fail,
        'ImageTooLarge': ImageTooLarge,
        'InactiveProject': ProjectInactive,
        'MetadataTooLarge': MetadataTooLarge,
        'ProjectHasNoAPIAccess': ProjectHasNoAPIAccess,
        'ProjectInactive': ProjectInactive,
        'ProjectSuspended': ProjectSuspended,
        'RequestQuotaReached': RequestQuotaReached,
        'RequestTimeTooSkewed': RequestTimeTooSkewed,
        'TargetNameExist': TargetNameExist,
        'TargetQuotaReached': TargetQuotaReached,
        'TargetStatusNotSuccess': TargetStatusNotSuccess,
        'TargetStatusProcessing': TargetStatusProcessing,
        'UnknownTarget': UnknownTarget,
    }[result_code]

    raise exception(response=response)
