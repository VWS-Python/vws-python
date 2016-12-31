"""
Tests for passing invalid endpoints which require a target ID to be given.
"""

from urllib.parse import urljoin

import pytest
import requests
from requests import codes

from common.constants import ResultCodes
from tests.mock_vws.utils import Endpoint, assert_vws_failure
from tests.utils import VuforiaServerCredentials
from vws._request_utils import authorization_header, rfc_1123_date


# @pytest.mark.usefixtures('verify_mock_vuforia')
class TestInvalidGivenID:
    """
    Tests for giving an invalid ID to endpoints which require a target ID to
    be given.
    """

    from mock_vws import MockVWS
    @MockVWS()
    def test_not_real_id(self,
                         vuforia_server_credentials: VuforiaServerCredentials,
                         endpoint_which_takes_target_id: Endpoint,  # noqa: E501 pylint: disable=redefined-outer-name
                         ) -> None:
        """
        A `NOT_FOUND` error is returned when an endpoint is given a target ID
        of a target which does not exist.
        """
        # request_path = endpoint_which_takes_target_id.example_path
        # date = rfc_1123_date()
        #
        # authorization_string = authorization_header(
        #     access_key=vuforia_server_credentials.access_key,
        #     secret_key=vuforia_server_credentials.secret_key,
        #     method=endpoint_which_takes_target_id.method,
        #     content=endpoint_which_takes_target_id.content,
        #     content_type=endpoint_which_takes_target_id.content_type or '',
        #     date=date,
        #     request_path=request_path,
        # )
        #
        # headers = {
        #     "Authorization": authorization_string,
        #     "Date": date,
        # }
        #
        # url = urljoin('https://vws.vuforia.com/', request_path)
        # response = requests.request(
        #     method=endpoint_which_takes_target_id.method,
        #     url=url,
        #     headers=headers,
        #     data=endpoint_which_takes_target_id.content,
        # )
        #
        # assert_vws_failure(
        #     response=response,
        #     status_code=codes.NOT_FOUND,
        #     result_code=ResultCodes.UNKNOWN_TARGET,
        # )
        import io, random, base64, json
        from PIL import Image
        request_path = '/targets'
        method = 'POST'

        image_buffer = io.BytesIO()

        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        width = 1
        height = 1

        image = Image.new('RGB', (width, height), color=(red, green, blue))
        image.save(image_buffer, 'PNG')
        image_buffer.seek(0)
        png_file = image_buffer
        image_data = png_file.read()
        image_data = base64.b64encode(image_data).decode('ascii')
        data = {
            'name': 'example_name',
            'width': 1,
            'image': image_data,

        }
        content = bytes(json.dumps(data), encoding='utf-8')

        date = rfc_1123_date()

        authorization_string = authorization_header(
            access_key=vuforia_server_credentials.access_key,
            secret_key=vuforia_server_credentials.secret_key,
            method=method,
            content=content,
            content_type='application/json',
            date=date,
            request_path=request_path,
        )

        headers = {
            "Authorization": authorization_string,
            "Date": date,
            'Content-Type': 'application/json',
        }

        url = urljoin('https://vws.vuforia.com/', request_path)
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=content,
        )

        import pdb; pdb.set_trace()
        # assert_vws_failure(
        #     response=response,
        #     status_code=codes.NOT_FOUND,
        #     result_code=ResultCodes.UNKNOWN_TARGET,
        # )
