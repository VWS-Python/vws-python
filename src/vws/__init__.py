"""A library for Vuforia Web Services."""

from .async_model_target_service import AsyncModelTargetService
from .async_query import AsyncCloudRecoService
from .async_vumark_service import AsyncVuMarkService
from .async_vws import AsyncVWS
from .model_target_service import ModelTargetService
from .query import CloudRecoService
from .vumark_service import VuMarkService
from .vws import VWS

__all__ = [
    "VWS",
    "AsyncCloudRecoService",
    "AsyncModelTargetService",
    "AsyncVWS",
    "AsyncVuMarkService",
    "CloudRecoService",
    "ModelTargetService",
    "VuMarkService",
]
