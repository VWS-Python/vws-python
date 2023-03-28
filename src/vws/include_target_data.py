"""
Tools for managing ``CloudRecoService.query``'s ``include_target_data``.
"""


from enum import StrEnum, auto


class CloudRecoIncludeTargetData(StrEnum):
    """
    Options for the ``include_target_data`` parameter of
    ``CloudRecoService.query``.
    """

    TOP = auto()
    NONE = auto()
    ALL = auto()
