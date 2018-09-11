from mock_vws import MockVWS
from requests import codes

from vws import VWS
from vws.exceptions import VWSException
import io
import pytest

# @hypothesis?
def test_add_target(high_quality_image: io.BytesIO) -> None:
    with MockVWS() as mock:
        client = VWS(
            server_access_key=mock.server_access_key,
            server_secret_key=mock.server_secret_key,
        )

        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

def test_authentication_error(high_quality_image: io.BytesIO) -> None:
    with MockVWS() as mock:
        client = VWS(
            server_access_key='a',
            server_secret_key=mock.server_secret_key,
        )

        with pytest.raises(VWSException) as exc:
            target_id = client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )

        assert exc.value.response.status_code == codes.BAD_REQUEST


def test_clock_skew() -> None:
    pass

def test_width_invalid() -> None:
    pass

class TestTargetName:
    pass
