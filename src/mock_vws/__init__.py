"""
Tools for using a fake implementation of Vuforia.
"""

import os
import re
from contextlib import ContextDecorator
from urllib.parse import urljoin

from typing import Optional  # noqa: F401 This is used in a type hint.
from typing import Any, Callable, Tuple, TypeVar, Pattern

from constantly import NamedConstant, Names
from requests_mock.mocker import Mocker

from ._mock import MockVuforiaTargetAPI

_MOCK_VWS_TYPE = TypeVar('_MOCK_VWS_TYPE', bound='MockVWS')


class States(Names):
    """
    Constants representing various web service states.
    """

    WORKING = NamedConstant()

    # A project is inactive if the license key has been deleted.
    PROJECT_INACTIVE = NamedConstant()

    SERVICE_UNAVAILABLE = NamedConstant()
    REQUEST_QUOTA_REACHED = NamedConstant()
    INTERNAL_STATUS_ERROR = NamedConstant()


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

    def __init__(
        self, real_http: bool=False, state: States=States.WORKING
    ) -> None:
        """
        Args:
            real_http: Whether or not to forward requests to the real server if
                they are not handled by the mock.
                See
                http://requests-mock.readthedocs.io/en/latest/mocker.html#real-http-requests
            state: The state of the services being mocked.

        Attributes:
            real_http (bool): Whether or not to forward requests to the real
                server if they are not handled by the mock.
                See
                http://requests-mock.readthedocs.io/en/latest/mocker.html#real-http-requests
            mock: None or an `requests_mock` object used for mocking Vuforia.
            state: The state of the services being mocked.
        """
        super().__init__()
        self.real_http = real_http
        self.mock = None  # type: Optional[Mocker]
        self.state = state

    def __call__(self, func: Callable[..., Any]) -> Any:
        """
        Override call to allow a wrapped function to return any type.
        """
        return super().__call__(func)

    def __enter__(self: _MOCK_VWS_TYPE) -> _MOCK_VWS_TYPE:
        """
        Start an instance of a Vuforia mock with access keys set from
        environment variables.

        Returns:
            ``self``.
        """
        fake_target_api = MockVuforiaTargetAPI(
            database_name=os.environ['VUFORIA_TARGET_MANAGER_DATABASE_NAME'],
            access_key=os.environ['VUFORIA_SERVER_ACCESS_KEY'],
            secret_key=os.environ['VUFORIA_SERVER_SECRET_KEY'],
        )

        headers = {
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Server': 'nginx',
        }
        with Mocker(real_http=self.real_http) as mock:
            if self.state == States.WORKING:
                for route in fake_target_api.routes:
                    for http_method in route.methods:
                        mock.register_uri(
                            method=http_method,
                            url=_target_endpoint_pattern(route.path_pattern),
                            text=getattr(fake_target_api, route.route_name),
                            headers=headers,
                        )

            if self.state == States.PROJECT_INACTIVE:
                pass

            if self.state == States.SERVICE_UNAVAILABLE:
                pass

            if self.state == States.REQUEST_QUOTA_REACHED:
                pass

            if self.state == States.INTERNAL_STATUS_ERROR:
                pass

        self.mock = mock
        self.mock.start()
        return self

    def __exit__(self, *exc: Tuple[None, None, None]) -> bool:
        """
        Stop the Vuforia mock.

        Returns:
            False
        """
        self.mock.stop()
        return False
