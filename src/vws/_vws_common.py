"""Shared helpers for VWS client implementations."""

import base64
import json
from typing import NoReturn

from vws._image_utils import ImageType, get_image_data
from vws.exceptions.vws_exceptions import (
    AuthenticationFailureError,
    BadImageError,
    BadRequestError,
    DateRangeError,
    FailError,
    ImageTooLargeError,
    InvalidAcceptHeaderError,
    InvalidInstanceIdError,
    InvalidTargetTypeError,
    MetadataTooLargeError,
    ProjectHasNoAPIAccessError,
    ProjectInactiveError,
    ProjectSuspendedError,
    RequestQuotaReachedError,
    RequestTimeTooSkewedError,
    TargetNameExistError,
    TargetQuotaReachedError,
    TargetStatusNotSuccessError,
    TargetStatusProcessingError,
    UnknownTargetError,
)
from vws.response import Response


def raise_for_vws_result_code(
    result_code: str, response: Response
) -> NoReturn:
    """Raise the appropriate VWS exception for the given result code."""
    exception = {
        "AuthenticationFailure": AuthenticationFailureError,
        "BadImage": BadImageError,
        "BadRequest": BadRequestError,
        "DateRangeError": DateRangeError,
        "Fail": FailError,
        "ImageTooLarge": ImageTooLargeError,
        "MetadataTooLarge": MetadataTooLargeError,
        "ProjectHasNoAPIAccess": ProjectHasNoAPIAccessError,
        "ProjectInactive": ProjectInactiveError,
        "ProjectSuspended": ProjectSuspendedError,
        "RequestQuotaReached": RequestQuotaReachedError,
        "RequestTimeTooSkewed": RequestTimeTooSkewedError,
        "TargetNameExist": TargetNameExistError,
        "TargetQuotaReached": TargetQuotaReachedError,
        "TargetStatusNotSuccess": TargetStatusNotSuccessError,
        "TargetStatusProcessing": TargetStatusProcessingError,
        "UnknownTarget": UnknownTargetError,
    }[result_code]
    raise exception(response=response)


def raise_for_vumark_result_code(
    result_code: str, response: Response
) -> NoReturn:
    """Raise the appropriate VuMark exception for the given result
    code.
    """
    exception = {
        "AuthenticationFailure": AuthenticationFailureError,
        "BadRequest": BadRequestError,
        "DateRangeError": DateRangeError,
        "Fail": FailError,
        "InvalidAcceptHeader": InvalidAcceptHeaderError,
        "InvalidInstanceId": InvalidInstanceIdError,
        "InvalidTargetType": InvalidTargetTypeError,
        "RequestTimeTooSkewed": RequestTimeTooSkewedError,
        "TargetStatusNotSuccess": TargetStatusNotSuccessError,
        "UnknownTarget": UnknownTargetError,
    }[result_code]
    raise exception(response=response)


def build_add_target_content(
    *,
    name: str,
    width: float,
    image: ImageType,
    active_flag: bool,
    application_metadata: str | None,
) -> bytes:
    """Build the request body for an add_target request."""
    image_data = get_image_data(image=image)
    image_data_encoded = base64.b64encode(s=image_data).decode(
        encoding="ascii",
    )
    data = {
        "name": name,
        "width": width,
        "image": image_data_encoded,
        "active_flag": active_flag,
        "application_metadata": application_metadata,
    }
    return json.dumps(obj=data).encode(encoding="utf-8")


def build_update_target_content(
    *,
    name: str | None,
    width: float | None,
    image: ImageType | None,
    active_flag: bool | None,
    application_metadata: str | None,
) -> bytes:
    """Build the request body for an update_target request."""
    data: dict[str, str | bool | float | int] = {}

    if name is not None:
        data["name"] = name

    if width is not None:
        data["width"] = width

    if image is not None:
        image_data = get_image_data(image=image)
        image_data_encoded = base64.b64encode(s=image_data).decode(
            encoding="ascii",
        )
        data["image"] = image_data_encoded

    if active_flag is not None:
        data["active_flag"] = active_flag

    if application_metadata is not None:
        data["application_metadata"] = application_metadata

    return json.dumps(obj=data).encode(encoding="utf-8")
