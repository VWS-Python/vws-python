"""
Tools for using a fake implementation of Vuforia.
"""

import re
import uuid
from contextlib import ContextDecorator
from urllib.parse import urljoin

from typing import Any, Callable, Optional, Pattern, Tuple, Union

from requests_mock.mocker import Mocker

from ._constants import States
from ._mock_web_services_api import MockVuforiaWebServicesAPI


def _target_endpoint_pattern(path_pattern: str) -> Pattern[str]:
    """
    Given a path pattern, return a regex which will match URLs to
    patch for the Target API.

    Args:
        path_pattern: A part of the url which can be matched for endpoints.
            For example `https://vws.vuforia.com/<this-part>`. This is
            compiled to be a regular expression, so it may be `/foo` or
            `/foo/.+` for example.
    """
    base = 'https://vws.vuforia.com/'  # type: str
    joined = urljoin(base=base, url=path_pattern + '$')
    return re.compile(joined)


class MockVWS(ContextDecorator):
    """
    Route requests to Vuforia's Web Service APIs to fakes of those APIs.

    This creates a mock which uses access keys from the environment.
    See the README to find which secrets to set.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        real_http: bool=False,
        state: States=States.WORKING,
        server_access_key: Optional[str]=None,
        server_secret_key: Optional[str]=None,
        database_name: Optional[str]=None,
        processing_time_seconds: Union[int, float]=0.5,
    ) -> None:
        """
        Args:
            real_http: Whether or not to forward requests to the real server if
                they are not handled by the mock.
                See
                http://requests-mock.readthedocs.io/en/latest/mocker.html#real-http-requests
            state: The state of the services being mocked.
            database_name: The name of the mock VWS target manager database.
                By default this is a random string.
            server_access_key: A VWS server access key for the mock.
            server_secret_key: A VWS server secret key for the mock.
            processing_time_seconds: The number of seconds to process each
                image for. In the real Vuforia Web Services, this is not
                deterministic.

        Attributes:
            server_access_key (str): A VWS server access key for the mock.
            server_secret_key (str): A VWS server secret key for the mock.
            database_name (str): The name of the mock VWS target manager
                database.
        """
        super().__init__()

        if database_name is None:
            database_name = uuid.uuid4().hex

        if server_access_key is None:
            server_access_key = uuid.uuid4().hex

        if server_secret_key is None:
            server_secret_key = uuid.uuid4().hex

        self._real_http = real_http
        self._mock = Mocker()
        self._state = state
        self._processing_time_seconds = processing_time_seconds

        self.server_access_key = server_access_key
        self.server_secret_key = server_secret_key
        self.database_name = database_name

    def __call__(  # pylint: disable=useless-super-delegation
        self,
        func: Callable[..., Any],
    ) -> Any:
        """
        Override call to allow a wrapped function to return any type.
        """
        return super(MockVWS, self).__call__(func)

    def __enter__(self) -> 'MockVWS':
        """
        Start an instance of a Vuforia mock with access keys set from
        environment variables.

        Returns:
            ``self``.
        """
        fake_target_api = MockVuforiaWebServicesAPI(
            database_name=self.database_name,
            server_access_key=self.server_access_key,
            server_secret_key=self.server_secret_key,
            state=self._state,
            processing_time_seconds=self._processing_time_seconds,
        )

        headers = {
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Server': 'nginx',
        }

        with Mocker(real_http=self._real_http) as mock:
            for route in fake_target_api.routes:
                for http_method in route.http_methods:
                    mock.register_uri(
                        method=http_method,
                        url=_target_endpoint_pattern(route.path_pattern),
                        text=getattr(fake_target_api, route.route_name),
                        headers=headers,
                    )

        self._mock = mock
        self._mock.start()
        return self

    def __exit__(self, *exc: Tuple[None, None, None]) -> bool:
        """
        Stop the Vuforia mock.

        Returns:
            False
        """
        # __exit__ needs this to be passed in but vulture thinks that it is
        # unused, so we "use" it here.
        for _ in (exc, ):
            pass

        self._mock.stop()
        return False
