"""
Tools for using a fake implementation of Vuforia.
"""

import os
from contextlib import ContextDecorator
from urllib.parse import urljoin
import re

from typing import Optional  # noqa: F401 This is used in a type hint.
from typing import Tuple, TypeVar, Pattern

from requests_mock.mocker import Mocker
from requests_mock import GET

from ._mock import MockVuforiaTargetAPI


_MockVWSType = TypeVar('_MockVWSType', bound='MockVWS')  # noqa: E501 pylint: disable=invalid-name


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
    joined = urljoin(base=base, url=path_pattern)
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

    def __init__(self, real_http: bool=False) -> None:
        """
        Args:
            real_http: Whether or not to forward requests to the real server if
            they are not handled by the mock.
            See
            http://requests-mock.readthedocs.io/en/latest/mocker.html#real-http-requests

        Attributes:
            real_http (bool): Whether or not to forward requests to the real
            server if they are not handled by the mock.
            See
            http://requests-mock.readthedocs.io/en/latest/mocker.html#real-http-requests
            req: None or an `requests_mock` object used for mocking Vuforia.
        """
        super().__init__()
        self.real_http = real_http
        self.req = None  # type: Optional[Mocker]

    def __enter__(self: _MockVWSType) -> _MockVWSType:
        """
        Start an instance of a Vuforia mock with access keys set from
        environment variables.

        Returns:
            ``self``.
        """
        fake_target_api = MockVuforiaTargetAPI(
            access_key=os.environ['VUFORIA_SERVER_ACCESS_KEY'],
            secret_key=os.environ['VUFORIA_SERVER_SECRET_KEY'],
        )
        from functools import partial

        with Mocker(real_http=self.real_http) as req:
            for route in fake_target_api.routes:
                for http_method in route.methods:
                    req.register_uri(
                        method=http_method,
                        url=_target_endpoint_pattern(route.path_pattern),
                        text=partial(route.route, fake_target_api),
                    )
        self.req = req
        self.req.start()
        return self

    def __exit__(self, *exc: Tuple[None, None, None]) -> bool:
        """
        Stop the Vuforia mock.

        Returns:
            False
        """
        self.req.stop()
        return False
