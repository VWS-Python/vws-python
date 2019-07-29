"""
Tools for managing result codes.
"""

from requests import Response

from vws.exceptions import (
    AuthenticationFailure,
    BadImage,
    Fail,
    ImageTooLarge,
    MetadataTooLarge,
    ProjectInactive,
    TargetNameExist,
    TargetStatusNotSuccess,
    TargetStatusProcessing,
    UnknownTarget,
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
    """
    result_code = response.json()['result_code']
    if result_code == expected_result_code:
        return

    exception = {
        'AuthenticationFailure': AuthenticationFailure,
        'BadImage': BadImage,
        'Fail': Fail,
        'ImageTooLarge': ImageTooLarge,
        'MetadataTooLarge': MetadataTooLarge,
        'ProjectInactive': ProjectInactive,
        'TargetNameExist': TargetNameExist,
        'TargetStatusProcessing': TargetStatusProcessing,
        'TargetStatusNotSuccess': TargetStatusNotSuccess,
        'UnknownTarget': UnknownTarget,
    }[result_code]

    raise exception(response=response)
