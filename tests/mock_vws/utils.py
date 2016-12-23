"""
Utilities for tests for the VWS mock.
"""

from string import hexdigits


def is_valid_transaction_id(string: str) -> bool:
    """
    Return whether or not a given string could be a valid Vuforia transaction
    id.

    A valid transaction id looks something like:

        dde268b0136e4c03aedfdaf3cb465815

    Args:
        string: A string to check for whether it is a valid transaction id.

    Returns:
        Whether or not a given string could be a valid Vuforia transaction id.
    """
    if len(string) != 32:
        return False

    return all(char in hexdigits for char in string)
