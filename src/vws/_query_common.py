"""Shared helpers for CloudReco query implementations."""

import datetime
import json
from typing import NoReturn

from vws.exceptions.cloud_reco_exceptions import (
    AuthenticationFailureError,
    BadImageError,
    InactiveProjectError,
    RequestTimeTooSkewedError,
)
from vws.reports import QueryResult, TargetData
from vws.response import Response


def raise_for_cloud_reco_result_code(
    result_code: str, response: Response
) -> NoReturn:
    """Raise the appropriate cloud reco exception for the given result
    code.
    """
    exception = {
        "AuthenticationFailure": AuthenticationFailureError,
        "BadImage": BadImageError,
        "InactiveProject": InactiveProjectError,
        "RequestTimeTooSkewed": RequestTimeTooSkewedError,
    }[result_code]
    raise exception(response=response)


def parse_query_results(text: str) -> list[QueryResult]:
    """Parse the results list from a cloud reco query response body."""
    result: list[QueryResult] = []
    result_list = list(json.loads(s=text)["results"])
    for item in result_list:
        target_data: TargetData | None = None
        if "target_data" in item:
            target_data_dict = item["target_data"]
            metadata = target_data_dict["application_metadata"]
            timestamp_string = target_data_dict["target_timestamp"]
            target_timestamp = datetime.datetime.fromtimestamp(
                timestamp=timestamp_string,
                tz=datetime.UTC,
            )
            target_data = TargetData(
                name=target_data_dict["name"],
                application_metadata=metadata,
                target_timestamp=target_timestamp,
            )

        query_result = QueryResult(
            target_id=item["target_id"],
            target_data=target_data,
        )

        result.append(query_result)
    return result
