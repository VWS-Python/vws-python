"""Tools for managing ``VWS.generate_vumark_instance``'s ``accept``."""

from enum import StrEnum, unique

from beartype import beartype


@beartype
@unique
class VuMarkAccept(StrEnum):
    """
    Options for the ``accept`` parameter of
    ``VWS.generate_vumark_instance``.
    """

    PNG = "image/png"
    SVG = "image/svg+xml"
    PDF = "application/pdf"
