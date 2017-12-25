"""
Tests for the mock of the query endpoint.

https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query.
"""

def query_vws(
    vuforia_server_credentials: VuforiaServerCredentials,
    data: Dict[str, Any],
    content_type: str = 'application/json',
) -> Response:
    """
    Return a response from a request to the endpoint to add a target.

    Args:
        vuforia_server_credentials: The credentials to use to connect to
            Vuforia.
        data: The data to send, in JSON format, to the endpoint.
        content_type: The `Content-Type` header to use.

    Returns:
        The response returned by the API.
    """
    date = rfc_1123_date()
    request_path = '/targets'

    content = bytes(json.dumps(data), encoding='utf-8')

    authorization_string = authorization_header(
        access_key=vuforia_server_credentials.access_key,
        secret_key=vuforia_server_credentials.secret_key,
        method=POST,
        content=content,
        content_type=content_type,
        date=date,
        request_path=request_path,
    )

    headers = {
        'Authorization': authorization_string,
        'Date': date,
        'Content-Type': content_type,
    }

    response = requests.request(
        method=POST,
        url=urljoin('https://vws.vuforia.com/', request_path),
        headers=headers,
        data=content,
    )

    return response

class TestQuery:
    """
    XXX
    """

    """
    * Normal query
    * Maximum size PNG
    * Bad content type
    * Maximum size JPG
    * max_num_results
    * include_target_data
    * Active flag
    * Success: False
    """

    def test_no_results(
        self,
        vuforia_server_credentials: VuforiaServerCredentials,
        png_rgb_success: io.BytesIO,
    ):
        """
        XXX
        """
        image_data = png_rgb_success.read()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': 'my_example_name',
            'width': 1234,
            'image': image_data_encoded,
        }

        response = add_target_to_vws(
            vuforia_server_credentials=vuforia_server_credentials,
            data=data,
        )

        target_id = response.json()['target_id']

        wait_for_target_processed(
            vuforia_server_credentials=vuforia_server_credentials,
            target_id=target_id,
        )

        response = query()

        assert 'results' not in response.json()
