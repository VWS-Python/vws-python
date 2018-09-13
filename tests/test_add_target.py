import io

import pytest
from mock_vws import MockVWS, States
from requests import codes

from vws import VWS
from vws.exceptions import Fail, MetadataTooLarge, ProjectInactive, TargetNameExist


# @hypothesis?

@pytest.fixture()
def client() -> VWS:
    with MockVWS(real_http=False) as mock:
        client = VWS(
            server_access_key=mock.server_access_key,
            server_secret_key=mock.server_secret_key,
        )

        yield client

class TestSuccess:
    def test_add_target(self, client: VWS, high_quality_image: io.BytesIO) -> None:
        client.add_target(name='x', width=1, image=high_quality_image)

    def test_add_two_targets(self, client: VWS, high_quality_image: io.BytesIO) -> None:
        client.add_target(name='x', width=1, image=high_quality_image)
        client.add_target(name='a', width=1, image=high_quality_image)

class TestName:
    def test_add_two_targets_same_name(self, client: VWS, high_quality_image: io.BytesIO) -> None:
        client.add_target(name='x', width=1, image=high_quality_image)

        with pytest.raises(TargetNameExist) as exc:
            client.add_target(name='x', width=1, image=high_quality_image)

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

    def test_none(self, client: VWS, high_quality_image: io.BytesIO):
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=None,
        )

    def test_given(self, client: VWS, high_quality_image: io.BytesIO):
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=b'a',
        )

    def test_too_large(self, client: VWS, high_quality_image: io.BytesIO):
        with pytest.raises(MetadataTooLarge):
            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                application_metadata=b'a' * 1024 * 1024,
            )

class TestInactiveProject:
    def test_inactive_project(self, high_quality_image: io.BytesIO):
        with MockVWS(real_http=False, state=States.PROJECT_INACTIVE) as mock:
            client = VWS(
                server_access_key=mock.server_access_key,
                server_secret_key=mock.server_secret_key,
            )

            with pytest.raises(ProjectInactive):
                client.add_target(
                    name='x',
                    width=1,
                    image=high_quality_image,
                )
