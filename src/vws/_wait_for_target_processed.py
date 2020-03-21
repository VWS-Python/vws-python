"""
Tooling for waiting for a target to be processed.

It lives here rather than in ``vws.py`` to support Windows.
"""

from time import sleep
from typing import Optional

from wrapt_timeout_decorator import timeout

import vws
from vws.exceptions import TargetProcessingTimeout
from vws.reports import TargetStatuses


def _wait_for_target_processed(
    vws_client: 'vws.VWS',
    target_id: str,
    seconds_between_requests: float,
) -> None:
    """
    Wait indefinitely for a target to get past the processing stage.

    Args:
        vws_client: The VWS client to make requests with.
        target_id: The ID of the target to wait for.
        seconds_between_requests: The number of seconds to wait between
            requests made while polling the target status.

    Raises:
        ~vws.exceptions.AuthenticationFailure: The secret key is not
            correct.
        ~vws.exceptions.Fail: There was an error with the request. For
            example, the given access key does not match a known database.
        TimeoutError: The target remained in the processing stage for more
            than five minutes.
        ~vws.exceptions.UnknownTarget: The given target ID does not match a
            target in the database.
        ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
            time sent to Vuforia.
    """
    while True:
        report = vws_client.get_target_summary_report(target_id=target_id)
        if report.status != TargetStatuses.PROCESSING:
            return

        sleep(seconds_between_requests)


def foobar(
    vws_client: 'vws.VWS',
    timeout_seconds: Optional[float],
    seconds_between_requests: float,
    target_id: str,
) -> None:
    """
    Add Windows support.
    """

    @timeout(
        dec_timeout=timeout_seconds,
        timeout_exception=TargetProcessingTimeout,
        use_signals=False,
    )
    def decorated() -> None:
        _wait_for_target_processed(
            vws_client=vws_client,
            target_id=target_id,
            seconds_between_requests=seconds_between_requests,
        )

    decorated()
