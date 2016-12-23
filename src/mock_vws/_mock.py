"""
A fake implementation of VWS.
"""

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Pattern
from urllib.parse import urljoin

import maya
from requests import codes
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

from common.constants import ResultCodes
import wrapt


def target_endpoint_pattern(path_pattern: str) -> Pattern[str]:
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


@wrapt.decorator
def validate_date(wrapped, instance, args, kwargs) -> str:
    # import pdb; pdb.set_trace()
    request, context = args
    if 'Date' not in request.headers:
        context.status_code = codes.BAD_REQUEST  # noqa: E501 pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.FAIL.value,
        }
        return json.dumps(body)
    return wrapped(*args, **kwargs)


class MockVuforiaTargetAPI:  # pylint: disable=no-self-use
    """
    A fake implementation of the Vuforia Target API.

    This implementation is tied to the implementation of `requests_mock`.
    """

    DATABASE_SUMMARY_URL = target_endpoint_pattern(path_pattern='summary')  # noqa: E501  type: Pattern[str]

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

    @validate_date
    def database_summary(self,
                         request: _RequestObjectProxy,
                         context: _Context) -> str:
        """
        Fake implementation of
        https://library.vuforia.com/articles/Solution/How-To-Get-a-Database-Summary-Report-Using-the-VWS-API
        """
        body = {}  # type: Dict[str, str]

        # TODO - More strict date parsing - this must be RFC blah blah
        date_from_header = maya.when(request.headers['Date']).datetime()
        time_difference = datetime.now(tz=timezone.utc) - date_from_header
        maximum_time_difference = timedelta(minutes=5)

        if abs(time_difference) >= maximum_time_difference:
            context.status_code = codes.FORBIDDEN  # noqa: E501 pylint: disable=no-member

            body = {
                'transaction_id': uuid.uuid4().hex,
                'result_code': ResultCodes.REQUEST_TIME_TOO_SKEWED.value,
            }
            return json.dumps(body)

        context.status_code = codes.OK  # pylint: disable=no-member
        body = {
            'transaction_id': uuid.uuid4().hex,
            'result_code': ResultCodes.SUCCESS.value,
        }
        return json.dumps(body)
