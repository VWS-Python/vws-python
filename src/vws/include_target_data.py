"""
Tools for managing ``CloudRecoService.query``'s ``include_target_data``.
"""

from enum import Enum


class CloudRecoIncludeTargetData(Enum):
    """
    Options for the ``include_target_data`` parameter of
    ``CloudRecoService.query``.
    """

    TOP = 'top'
    NONE = 'none'
    ALL = 'all'
