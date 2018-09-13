import io

import pytest
from mock_vws import MockVWS
from requests import codes

from vws import VWS
from vws.exceptions import Fail, TargetNameExist


# @hypothesis?

class TestSuccess:
    def test_add_target(self, high_quality_image: io.BytesIO) -> None:
        with MockVWS() as mock:
            client = VWS(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
            )

            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )

    def test_add_two_targets(self, high_quality_image: io.BytesIO) -> None:
        with MockVWS() as mock:
            client = VWS(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
            )

            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )

            client.add_target(
                name='a',
                width=1,
                image=high_quality_image,
            )

class TestName:
    def test_add_two_targets_same_name(self, high_quality_image: io.BytesIO) -> None:
        with MockVWS() as mock:
            client = VWS(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
            )

            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )

            with pytest.raises(TargetNameExist) as exc:
                client.add_target(
                    name='x',
                    width=1,
                    image=high_quality_image,
                )

class TestAuthentication:
    def test_authentication_error(self, high_quality_image: io.BytesIO) -> None:
        with MockVWS() as mock:
            client = VWS(
                server_access_key='a',
                server_secret_key=mock.server_secret_key,
            )

            with pytest.raises(Fail) as exc:
                target_id = client.add_target(
                    name='x',
                    width=1,
                    image=high_quality_image,
                )

            exception = exc.value
            assert exception.response.status_code == codes.BAD_REQUEST

class TestImage:
    def test_image_too_large(self):
        pass

    def test_not_an_image(self):
        pass

class TestapplicationMetadata:

    def test_none(self):
        pass

    def test_given(self):
        pass

    def test_too_large(self):
        pass
