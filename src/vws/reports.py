"""Classes for representing Vuforia reports."""

import datetime as dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, unique
from typing import Self, TypeIs

from beartype import beartype
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
    created_at: dt.datetime
    eta: dt.datetime | None
    """When Vuforia expects to finish generating the dataset.

    This is given only while the dataset is processing.
    """

    completed_at: dt.datetime | None
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

        eta: dt.datetime | None = None
        if "eta" in response_dict:
            eta = dt.datetime.fromisoformat(
                _checked(response_dict["eta"], str),
            )

        completed_at: dt.datetime | None = None
        if "completedAt" in response_dict:
            completed_at = dt.datetime.fromisoformat(
                _checked(response_dict["completedAt"], str),
            )

        return cls(
            status=ModelTargetDatasetStatuses(
                value=_checked(response_dict["status"], str),
            ),
            dataset_uuid=_checked(response_dict["uuid"], str),
            created_at=dt.datetime.fromisoformat(
                _checked(response_dict["createdAt"], str),
            ),
            eta=eta,
            completed_at=completed_at,
            error=error,
            warning=warning,
        )
