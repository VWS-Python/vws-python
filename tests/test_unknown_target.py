"""
Tests for passing invalid target IDs to endpoints which
require a target ID to be given.
"""

from functools import partial

from vws import VWS


class TestInvalidGivenID:
    """
    Tests for giving an invalid ID to endpoints which require a target ID to
    be given.
    """

    def test_invalid_given_id(
        self,
        client: VWS,
    ):
        get_target_record = partial(client.get_target_record)

        funcs = (
            get_target_record,
        )

        for func in funcs:
            func(target_id='x')
