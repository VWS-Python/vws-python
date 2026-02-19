"""A library for Vuforia Web Services."""

from .query import CloudRecoService
from .vumark_service import VuMarkService
from .vws import VWS

__all__ = [
    "VWS",
    "CloudRecoService",
    "VuMarkService",
]
