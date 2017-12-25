"""
Tools for using a fake implementation of Vuforia.
"""

import re
import uuid
from contextlib import ContextDecorator
from urllib.parse import urljoin

from typing import Any, Callable, Optional, Pattern, Tuple, TypeVar

from requests_mock.mocker import Mocker

from ._constants import States
from ._mock import MockVuforiaTargetAPI

_MOCK_VWS_TYPE = TypeVar('_MOCK_VWS_TYPE', bound='MockVWS')


def _target_endpoint_pattern(host: str, path_pattern: str) -> Pattern[str]:
    """
    Given a path pattern, return a regex which will match URLs to patch for the
    Target API.

    Args:
        host: The host that the target endpoint is available on.
        path_pattern: A part of the url which can be matched for endpoints.
            For example `https://vws.vuforia.com/<this-part>`. This is
            compiled to be a regular expression, so it may be `/foo` or
            `/foo/.+` for example.
    """
    scheme = 'https://'
    joined = urljoin(base=scheme + host, url=path_pattern + '$')
    return re.compile(joined)


class MockVWS(ContextDecorator):
    """
    Route requests to Vuforia's Web Service APIs to fakes of those APIs.

    This creates a mock which uses access keys from the environment.
    See the README to find which secrets to set.

    This can be used as a context manager or as a decorator.

    Examples:
        >>> @MockVWS()
        ... def test_vuforia_example():
        ...     pass

        or

        >>> def test_vuforia_example():
        ...     with MockVWS():
        ...         pass
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        real_http: bool=False,
        state: States=States.WORKING,
        access_key: Optional[str]=None,
        secret_key: Optional[str]=None,
        database_name: Optional[str]=None,
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
            access_key: A VWS access key for the mock.
            secret_key: A VWS secret key for the mock.

        Attributes:
            access_key: A VWS access key for the mock.
            secret_key: A VWS secret key for the mock.
            database_name: The name of the mock VWS target manager database.
        """
        super().__init__()

        if database_name is None:
            database_name = uuid.uuid4().hex

        if access_key is None:
            access_key = uuid.uuid4().hex

        if secret_key is None:
            secret_key = uuid.uuid4().hex

        self._real_http = real_http
        self._mock = Mocker()
        self._state = state

        self.access_key = access_key
        self.secret_key = secret_key
        self.database_name = database_name

    def __call__(  # pylint: disable=useless-super-delegation
        self,
        func: Callable[..., Any],
    ) -> Any:
        """
        Override call to allow a wrapped function to return any type.
        """
        return super(MockVWS, self).__call__(func)

    def __enter__(self: _MOCK_VWS_TYPE) -> _MOCK_VWS_TYPE:
        """
        Start an instance of a Vuforia mock with access keys set from
        environment variables.

        Returns:
            ``self``.
        """
        fake_target_api = MockVuforiaTargetAPI(
            database_name=self.database_name,
            access_key=self.access_key,
            secret_key=self.secret_key,
            state=self._state,
        )

        headers = {
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Server': 'nginx',
        }

        with Mocker(real_http=self._real_http) as mock:
            for route in fake_target_api.routes:
                for http_method in route.http_methods:
                    url = _target_endpoint_pattern(
                        host=route.host,
                        path_pattern=route.path_pattern,
                    )

                    text = getattr(fake_target_api, name=route.route_name)

                    mock.register_uri(
                        method=http_method,
                        url=url,
                        text=text,
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
