"""
Tests for test utilities for the VWS mock.
"""

import string

from hypothesis import assume, given
from hypothesis.strategies import characters, text

from tests.mock_vws.utils import is_valid_transaction_id


class TestIsValidTransactionId:
    """
    Tests for `is_valid_transaction_id`.
    """

    def test_example(self):
        """
        A known test example is considered valid.
        """
        assert is_valid_transaction_id(
            string='dde268b0136e4c03aedfdaf3cb465815')

    @given(
        transaction_id=text(
            alphabet=string.hexdigits,
            min_size=32,
            max_size=32,
        ),
    )
    def test_32_character_hexadecimal(self, transaction_id: str) -> None:
        """
        32 character hexadecimals are considered valid.
        """
        assert is_valid_transaction_id(string=transaction_id)

    @given(transaction_id=text(alphabet=string.hexdigits))
    def test_incorrect_length(self, transaction_id: str) -> None:
        """
        A transaction id is not valid if it is not 32 characters long.
        """
        assume(len(transaction_id) != 32)
        assert not is_valid_transaction_id(string=transaction_id)

    @given(
        transaction_id=text(
            alphabet=string.hexdigits,
            min_size=32,
            max_size=32,
        ),
        invalid_character=characters(blacklist_characters=string.hexdigits),
    )
    def test_not_hexadecimal(self, transaction_id: str,
                             invalid_character: str) -> None:
        """
        Only hexdigits are allowed in a transaction id.
        """
        transaction_id = invalid_character + transaction_id[1:]
        assert not is_valid_transaction_id(string=transaction_id)
