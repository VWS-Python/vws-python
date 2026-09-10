"""Classes for representing Vuforia reports."""

import csv
import datetime
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, unique
from typing import Self, TypeIs

from beartype import BeartypeConf, beartype
from beartype.door import TypeHint

from vws.json_types import JSONValue


def _checked[T](value: object, hint: type[T], /) -> T:
    """Return a value after checking its runtime type."""
    if not _is_type(value, hint):
        msg = f"Expected {hint!r}, got {value!r}."
        raise TypeError(msg)
    return value


def _is_type[T](value: object, hint: type[T], /) -> TypeIs[T]:
    """Return whether a value satisfies a runtime type."""
    return TypeHint(hint=hint).is_bearable(obj=value)


def _number(value: object, /) -> int | float:
    """Return a runtime-validated JSON number."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"Expected a number, got {value!r}."
        raise TypeError(msg)
    return value


def _optional_string(value: object, /) -> str | None:
    """Return a runtime-validated optional string."""
    if value is not None and not isinstance(value, str):
        msg = f"Expected an optional string, got {value!r}."
        raise TypeError(msg)
    return value


@beartype
@dataclass(frozen=True, kw_only=True)
class DatabaseSummaryReport:
    """A database summary report.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#summary-report.
    """

    active_images: int
    current_month_recos: int
    failed_images: int
    inactive_images: int
    name: str
    previous_month_recos: int
    processing_images: int
    reco_threshold: int
    request_quota: int
    request_usage: int
    target_quota: int
    total_recos: int

    @classmethod
    def from_response_dict(
        cls, response_dict: Mapping[str, JSONValue]
    ) -> Self:
        """Construct from a VWS API response dict."""
        return cls(
            active_images=int(_number(response_dict["active_images"])),
            current_month_recos=int(
                _number(response_dict["current_month_recos"])
            ),
            failed_images=int(_number(response_dict["failed_images"])),
            inactive_images=int(_number(response_dict["inactive_images"])),
            name=_checked(response_dict["name"], str),
            previous_month_recos=int(
                _number(response_dict["previous_month_recos"])
            ),
            processing_images=int(_number(response_dict["processing_images"])),
            reco_threshold=int(_number(response_dict["reco_threshold"])),
            request_quota=int(_number(response_dict["request_quota"])),
            request_usage=int(_number(response_dict["request_usage"])),
            target_quota=int(_number(response_dict["target_quota"])),
            total_recos=int(_number(response_dict["total_recos"])),
        )


@beartype
@unique
class TargetStatuses(Enum):
    """Constants representing VWS target statuses.

    See the 'status' field in
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#target-record
    """

    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


@beartype
@dataclass(frozen=True, kw_only=True)
class TargetSummaryReport:
    """A target summary report.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#summary-report.
    """

    status: TargetStatuses
    database_name: str
    target_name: str
    upload_date: datetime.date
    active_flag: bool
    tracking_rating: int
    total_recos: int
    current_month_recos: int
    previous_month_recos: int

    @classmethod
    def from_response_dict(
        cls, response_dict: Mapping[str, JSONValue]
    ) -> Self:
        """Construct from a VWS API response dict."""
        return cls(
            status=TargetStatuses(
                value=_checked(response_dict["status"], str)
            ),
            database_name=_checked(response_dict["database_name"], str),
            target_name=_checked(response_dict["target_name"], str),
            upload_date=datetime.date.fromisoformat(
                _checked(response_dict["upload_date"], str)
            ),
            active_flag=bool(response_dict["active_flag"]),
            tracking_rating=int(_number(response_dict["tracking_rating"])),
            total_recos=int(_number(response_dict["total_recos"])),
            current_month_recos=int(
                _number(response_dict["current_month_recos"])
            ),
            previous_month_recos=int(
                _number(response_dict["previous_month_recos"])
            ),
        )


@beartype(conf=BeartypeConf(is_pep484_tower=True))
@dataclass(frozen=True, kw_only=True)
class TargetRecord:
    """A target record.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#target-record.
    """

    target_id: str
    active_flag: bool
    name: str
    width: float
    tracking_rating: int
    reco_rating: str


@beartype
@dataclass(frozen=True, kw_only=True)
class TargetData:
    """The target data optionally included with a query match."""

    name: str
    application_metadata: str | None
    target_timestamp: datetime.datetime


@beartype
@dataclass(frozen=True, kw_only=True)
class QueryResult:
    """One query match result.

    See
    https://developer.vuforia.com/library/web-api/vuforia-query-web-api.
    """

    target_id: str
    target_data: TargetData | None

    @classmethod
    def from_response_dict(
        cls,
        response_dict: Mapping[str, JSONValue],
    ) -> Self:
        """Construct from a VWS API query result item dict."""
        target_data: TargetData | None = None
        if "target_data" in response_dict:
            target_data_dict = _checked(
                response_dict["target_data"], dict[str, JSONValue]
            )
            target_timestamp = datetime.datetime.fromtimestamp(
                timestamp=_number(target_data_dict["target_timestamp"]),
                tz=datetime.UTC,
            )
            target_data = TargetData(
                name=_checked(target_data_dict["name"], str),
                application_metadata=_optional_string(
                    target_data_dict["application_metadata"]
                ),
                target_timestamp=target_timestamp,
            )
        return cls(
            target_id=_checked(response_dict["target_id"], str),
            target_data=target_data,
        )


@beartype
@dataclass(frozen=True, kw_only=True)
class TargetStatusAndRecord:
    """The target status and a target record.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api#target-record.
    """

    status: TargetStatuses
    target_record: TargetRecord

    @classmethod
    def from_response_dict(
        cls, response_dict: Mapping[str, JSONValue]
    ) -> Self:
        """Construct from a VWS API response dict."""
        status = TargetStatuses(value=_checked(response_dict["status"], str))
        target_record_dict = _checked(
            response_dict["target_record"], dict[str, JSONValue]
        )
        target_record = TargetRecord(
            target_id=_checked(target_record_dict["target_id"], str),
            active_flag=bool(target_record_dict["active_flag"]),
            name=_checked(target_record_dict["name"], str),
            width=float(_number(target_record_dict["width"])),
            tracking_rating=int(
                _number(target_record_dict["tracking_rating"])
            ),
            reco_rating=_checked(target_record_dict["reco_rating"], str),
        )
        return cls(status=status, target_record=target_record)


@beartype
@dataclass(frozen=True, kw_only=True)
class RecoCountsReportRequest:
    """A requested database reco counts report.

    See
    https://developer.vuforia.com/library/web-api/cloud-targets-web-services-api.
    """

    transaction_id: str
    presigned_url: str
    """The URL to download the report from.

    Real Vuforia's URLs expire just under seven days after the report is
    requested.
    """

    @classmethod
    def from_response_dict(
        cls, response_dict: Mapping[str, JSONValue]
    ) -> Self:
        """Construct from a VWS API response dict."""
        return cls(
            transaction_id=_checked(response_dict["transaction_id"], str),
            presigned_url=_checked(response_dict["presigned_url"], str),
        )


@beartype
@unique
class ModelTargetDatasetStatuses(Enum):
    """Constants representing Model Target dataset generation statuses.

    See the 'status' field of the dataset status response at
    https://developer.vuforia.com/library/vuforia-engine/web-api/model-target-web-api/.
    """

    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@beartype
@dataclass(frozen=True, kw_only=True)
class ModelTargetGenerationDetail:
    """One detail of a Model Target dataset generation warning."""

    code: str
    message: str


@beartype
@dataclass(frozen=True, kw_only=True)
class ModelTargetGenerationError:
    """The reason a Model Target dataset failed to generate."""

    code: str
    message: str


@beartype
@dataclass(frozen=True, kw_only=True)
class ModelTargetGenerationWarning:
    """A warning about a generated Model Target dataset.

    A dataset with a warning is generated, and can be downloaded.
    """

    code: str
    message: str
    target: str
    details: Sequence[ModelTargetGenerationDetail]


@beartype
@dataclass(frozen=True, kw_only=True)
class ModelTargetDatasetStatusReport:
    """The status of a Model Target dataset.

    See
    https://developer.vuforia.com/library/vuforia-engine/web-api/model-target-web-api/.
    """

    status: ModelTargetDatasetStatuses
    dataset_uuid: str
    created_at: datetime.datetime
    eta: datetime.datetime | None
    """When Vuforia expects to finish generating the dataset.

    This is given only while the dataset is processing.
    """

    completed_at: datetime.datetime | None
    """When Vuforia finished generating the dataset.

    This is given only once the dataset is no longer processing.
    """

    error: ModelTargetGenerationError | None
    """Why the dataset failed to generate.

    This is given only for a failed dataset.
    """

    warning: ModelTargetGenerationWarning | None
    """A warning about the generated dataset.

    This is given only for a generated dataset which has a warning.
    """

    @classmethod
    def from_response_dict(
        cls,
        response_dict: Mapping[str, JSONValue],
    ) -> Self:
        """Construct from a Model Target Web API response dict."""
        error: ModelTargetGenerationError | None = None
        if "error" in response_dict:
            error_dict = _checked(response_dict["error"], dict[str, JSONValue])
            error = ModelTargetGenerationError(
                code=_checked(error_dict["code"], str),
                message=_checked(error_dict["message"], str),
            )

        warning: ModelTargetGenerationWarning | None = None
        if "warning" in response_dict:
            warning_dict = _checked(
                response_dict["warning"], dict[str, JSONValue]
            )
            details = _checked(
                warning_dict["details"], list[dict[str, JSONValue]]
            )
            warning = ModelTargetGenerationWarning(
                code=_checked(warning_dict["code"], str),
                message=_checked(warning_dict["message"], str),
                target=_checked(warning_dict["target"], str),
                details=[
                    ModelTargetGenerationDetail(
                        code=_checked(detail["code"], str),
                        message=_checked(detail["message"], str),
                    )
                    for detail in details
                ],
            )

        eta: datetime.datetime | None = None
        if "eta" in response_dict:
            eta = datetime.datetime.fromisoformat(
                _checked(response_dict["eta"], str),
            )

        completed_at: datetime.datetime | None = None
        if "completedAt" in response_dict:
            completed_at = datetime.datetime.fromisoformat(
                _checked(response_dict["completedAt"], str),
            )

        return cls(
            status=ModelTargetDatasetStatuses(
                value=_checked(response_dict["status"], str),
            ),
            dataset_uuid=_checked(response_dict["uuid"], str),
            created_at=datetime.datetime.fromisoformat(
                _checked(response_dict["createdAt"], str),
            ),
            eta=eta,
            completed_at=completed_at,
            error=error,
            warning=warning,
        )


@beartype
@dataclass(frozen=True, kw_only=True)
class RecoCount:
    """The number of recognitions of one target in a reco counts
    report.
    """

    target_id: str
    reco_count: int


@beartype
@dataclass(frozen=True, kw_only=True)
class RecoCountsReport:
    """A downloaded database reco counts report.

    A report for a month with no recognitions has no ``reco_counts``.
    """

    reco_counts: Sequence[RecoCount]
    raw_csv: bytes
    """The downloaded CSV, before it was parsed.

    Vuforia does not document the format of the report, so it may include
    columns which ``reco_counts`` does not expose.
    """

    @classmethod
    def from_csv(cls, csv_bytes: bytes) -> Self:
        """Construct from the CSV content of a downloaded report."""
        text = csv_bytes.decode(encoding="utf-8")
        reader = csv.DictReader(f=io.StringIO(initial_value=text, newline=""))
        reco_counts = [
            RecoCount(
                target_id=row["target_id"],
                reco_count=int(row["reco_count"]),
            )
            for row in reader
        ]
        return cls(reco_counts=reco_counts, raw_csv=csv_bytes)
