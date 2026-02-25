"""Shared helpers for CloudReco query implementations."""

from typing import NoReturn

from vws.exceptions.cloud_reco_exceptions import (
    AuthenticationFailureError,
    BadImageError,
    InactiveProjectError,
    RequestTimeTooSkewedError,
)
from vws.response import Response


def raise_for_cloud_reco_result_code(
    result_code: str, response: Response
) -> NoReturn:
    """Raise the appropriate cloud reco exception for the given result
    code.
    """
    exception = {
        "AuthenticationFailure": AuthenticationFailureError,
        "BadImage": BadImageError,
        "InactiveProject": InactiveProjectError,
        "RequestTimeTooSkewed": RequestTimeTooSkewedError,
    }[result_code]
    raise exception(response=response)
