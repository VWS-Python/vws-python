"""Shared helpers for VWS client implementations."""

import base64
import json
from datetime import date
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
from vws.reports import (
    DatabaseSummaryReport,
    TargetRecord,
    TargetStatusAndRecord,
    TargetStatuses,
    TargetSummaryReport,
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


def parse_target_record_response(text: str) -> TargetStatusAndRecord:
    """Parse a get_target_record response body."""
    result_data = json.loads(s=text)
    status = TargetStatuses(value=result_data["status"])
    target_record_dict = dict(result_data["target_record"])
    target_record = TargetRecord(
        target_id=target_record_dict["target_id"],
        active_flag=bool(target_record_dict["active_flag"]),
        name=target_record_dict["name"],
        width=float(target_record_dict["width"]),
        tracking_rating=int(target_record_dict["tracking_rating"]),
        reco_rating=target_record_dict["reco_rating"],
    )
    return TargetStatusAndRecord(
        status=status,
        target_record=target_record,
    )


def parse_target_summary_response(text: str) -> TargetSummaryReport:
    """Parse a get_target_summary_report response body."""
    result_data = dict(json.loads(s=text))
    return TargetSummaryReport(
        status=TargetStatuses(value=result_data["status"]),
        database_name=result_data["database_name"],
        target_name=result_data["target_name"],
        upload_date=date.fromisoformat(result_data["upload_date"]),
        active_flag=bool(result_data["active_flag"]),
        tracking_rating=int(result_data["tracking_rating"]),
        total_recos=int(result_data["total_recos"]),
        current_month_recos=int(result_data["current_month_recos"]),
        previous_month_recos=int(result_data["previous_month_recos"]),
    )


def parse_database_summary_response(text: str) -> DatabaseSummaryReport:
    """Parse a get_database_summary_report response body."""
    response_data = dict(json.loads(s=text))
    return DatabaseSummaryReport(
        active_images=int(response_data["active_images"]),
        current_month_recos=int(response_data["current_month_recos"]),
        failed_images=int(response_data["failed_images"]),
        inactive_images=int(response_data["inactive_images"]),
        name=str(object=response_data["name"]),
        previous_month_recos=int(response_data["previous_month_recos"]),
        processing_images=int(response_data["processing_images"]),
        reco_threshold=int(response_data["reco_threshold"]),
        request_quota=int(response_data["request_quota"]),
        request_usage=int(response_data["request_usage"]),
        target_quota=int(response_data["target_quota"]),
        total_recos=int(response_data["total_recos"]),
    )


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
