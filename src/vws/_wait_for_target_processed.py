"""
This is tooling for waiting for a target to be processed.

It lives here rather than in ``vws.py`` to support Windows.
"""

from typing import Optional

from wrapt_timeout_decorator import timeout

from vws import VWS
from vws.exceptions import TargetProcessingTimeout


def foobar(
    vws_client: VWS,
    timeout_seconds: Optional[float],
    seconds_between_requests: float,
    target_id: str,
):

    @timeout(
        dec_timeout=timeout_seconds,
        timeout_exception=TargetProcessingTimeout,
        use_signals=False,
    )
    def decorated() -> None:
        vws_client._wait_for_target_processed(
            target_id=target_id,
            seconds_between_requests=seconds_between_requests,
        )

    decorated()
