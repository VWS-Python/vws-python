"""
Tools for using a fake implementation of Vuforia.
"""

import os
import re
from contextlib import contextmanager
from urllib.parse import urljoin

from typing import Iterator, Pattern

import requests_mock
from requests_mock import GET

from requests import codes


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


class FakeVuforiaTargetAPI:
    """
    A fake implementation of the Vuforia Target API.

    This implementation is tied to the implementation of `requests_mock`.
    """

    DATABASE_SUMMARY_URL = _target_endpoint_pattern(path_pattern='summary')  # noqa type: Pattern[str]

    def __init__(self, access_key: str, secret_key: str) -> None:
        """
        Args:
            access_key: A VWS access key.
            secret_key: A VWS secret key.

        Attributes:
            access_key: A VWS access key.
            secret_key: A VWS secret key.
        """
        self.access_key = access_key  # type: str
        self.secret_key = secret_key  # type: str

    def database_summary(self,
                         request: requests_mock.request._RequestObjectProxy,  # noqa pylint: disable=unused-argument
                         context: requests_mock.response._Context) -> str:
        """
        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Get-a-Database-Summary-Report-Using-the-VWS-API  # noqa pylint: disable=line-too-long
        """
        context.status_code = codes.OK
        return '{}'


@contextmanager
def mock_vws(real_http: bool=False) -> Iterator[object]:
    """
    Route requests to Vuforia's Web Service APIs to fakes of those APIs.

    This creates a mock which uses access keys from the environment.
    See the README to find which secrets to set.

    Args:
        real_http: Whether or not to forward requests to the real server if
            they are not handled by the mock.
            http://requests-mock.readthedocs.io/en/latest/mocker.html#real-http-requests  # noqa

    This can be used as a context manager or as a decorator.

    Examples:

        >>> @mock_vuforia
        ... def test_vuforia_example():
        ...     pass

        or

        >>> def test_vuforia_example():
        ...     with mock_vuforia():
        ...         pass
    """
    fake_target_api = FakeVuforiaTargetAPI(
        access_key=os.environ['VUFORIA_SERVER_ACCESS_KEY'],
        secret_key=os.environ['VUFORIA_SERVER_SECRET_KEY'],
    )
    real_http = False
    with requests_mock.Mocker(real_http=real_http) as req:
        req.register_uri(
            method=GET,
            url=fake_target_api.DATABASE_SUMMARY_URL,
            text=fake_target_api.database_summary,
        )
        # We need to yield an iterator to satisfy `mypy`.
        yield []
