from mock_vws import MockVWS

from vws import VWS

# @hypothesis?
def test_add_target() -> None:
    with MockVWS() as mock:
        client = VWS(
            server_access_key=mock.server_access_key,
            server_secret_key=mock.server_secret_key,
        )

        target_id = client.add_target(
            name=b'x',
            width='x',
            image=b'x',
        )

def test_authentication_error() -> None:
    pass

def test_clock_skew() -> None:
    pass

def test_width_invalid() -> None:
    pass

class TestTargetName:
    pass
