"""Structures for describing Model Target datasets to create.

See
https://developer.vuforia.com/library/vuforia-engine/web-api/model-target-web-api/.
"""

from collections.abc import Sequence  # noqa: TC003
from dataclasses import dataclass
from enum import StrEnum, unique

from beartype import BeartypeConf, beartype


@beartype
@unique
class ModelTargetDatasetType(StrEnum):
    """The kinds of Model Target dataset which Vuforia generates.

    Standard and advanced datasets are separate resources, so a dataset
    created as one type is not visible to requests for the other type.
    """

    STANDARD = "standard"
    ADVANCED = "advanced"


@beartype
@unique
class AutomaticColoring(StrEnum):
    """Options for a model's ``automaticColoring``."""

    ALWAYS = "always"
    AUTO = "auto"
    NEVER = "never"


@beartype
@unique
class CadDataFormat(StrEnum):
    """Options for a model's ``cadDataFormat``."""

    DAE = "DAE"
    FBX = "FBX"
    GLB = "GLB"
    IGES = "IGES"
    OBJ = "OBJ"
    PVZ = "PVZ"
    STL = "STL"
    VRML = "VRML"
    ZIP = "ZIP"


@beartype
@unique
class MotionHint(StrEnum):
    """Options for a model's ``motionHint``."""

    ADAPTIVE = "adaptive"
    DYNAMIC = "dynamic"
    STATIC = "static"


@beartype
@unique
class OptimizeTrackingFor(StrEnum):
    """Options for a model's ``optimizeTrackingFor``."""

    AR_CONTROLLER = "ar_controller"
    DEFAULT = "default"
    LOW_FEATURE_OBJECTS = "low_feature_objects"


@beartype
@unique
class RealisticAppearance(StrEnum):
    """Options for a model's ``realisticAppearance``.

    This is documented for advanced datasets only.
    """

    AUTO = "auto"
    FALSE = "false"
    TRUE = "true"


@beartype
@unique
class Simplify(StrEnum):
    """Options for a model's ``simplify``."""

    ALWAYS = "always"
    AUTO = "auto"
    NEVER = "never"


@beartype
@unique
class TrackingMode(StrEnum):
    """Options for a model's ``trackingMode``."""

    CAR = "car"
    DEFAULT = "default"
    SCAN = "scan"


@beartype(conf=BeartypeConf(is_pep484_tower=True))
@dataclass(frozen=True, kw_only=True)
class GuideViewPosition:
    """The position of a guide view."""

    rotation: Sequence[float]
    translation: Sequence[float]


@beartype
@dataclass(frozen=True, kw_only=True)
class ModelTargetView:
    """A guide view of a model."""

    name: str
    guide_view_position: GuideViewPosition
    states: Sequence[str] | None = None
    """The State-Based Model Target states which this view applies to.

    Every given state must be named by the model's
    ``state_based_configuration_json_string``.
    """


@beartype
@dataclass(frozen=True, kw_only=True)
class ModelTargetModel:
    """A model to generate a Model Target dataset from.

    One and only one of ``cad_data_url`` and ``cad_data_blob`` is
    required.
    """

    name: str
    cad_data_url: str | None = None
    cad_data_blob: str | None = None
    automatic_coloring: AutomaticColoring | None = None
    cad_data_format: CadDataFormat | None = None
    motion_hint: MotionHint | None = None
    optimize_tracking_for: OptimizeTrackingFor | None = None
    realistic_appearance: RealisticAppearance | None = None
    """This is documented for advanced datasets only."""

    simplify: Simplify | None = None
    tracking_mode: TrackingMode | None = None
    state_based_configuration_json_string: str | None = None
    views: Sequence[ModelTargetView] | None = None
