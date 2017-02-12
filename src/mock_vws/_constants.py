"""
Constants used to make the VWS mock.
"""

from constantly import NamedConstant, Names


class States(Names):
    """
    Constants representing various web service states.
    """

    WORKING = NamedConstant()

    # A project is inactive if the license key has been deleted.
    PROJECT_INACTIVE = NamedConstant()
