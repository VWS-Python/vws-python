"""
Tools for interacting with Vuforia APIs.
"""

import base64
import io
import json
from datetime import date
from time import sleep
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from func_timeout import func_set_timeout
from func_timeout.exceptions import FunctionTimedOut
from requests import Response
from vws_auth_tools import authorization_header, rfc_1123_date

from vws._result_codes import raise_for_result_code
from vws.exceptions import TargetProcessingTimeout
from vws.reports import (
    DatabaseSummaryReport,
    TargetRecord,
    TargetStatuses,
    TargetSummaryReport,
)


def _target_api_request(
    server_access_key: str,
    server_secret_key: str,
    method: str,
    content: bytes,
    request_path: str,
    base_vws_url: str,
) -> Response:
    """
    Make a request to the Vuforia Target API.

    This uses `requests` to make a request against https://vws.vuforia.com.
    The content type of the request will be `application/json`.

    Args:
        server_access_key: A VWS server access key.
        server_secret_key: A VWS server secret key.
        method: The HTTP method which will be used in the request.
        content: The request body which will be used in the request.
        request_path: The path to the endpoint which will be used in the
            request.
        base_vws_url: The base URL for the VWS API.

    Returns:
        The response to the request made by `requests`.
    """
    date_string = rfc_1123_date()
    content_type = 'application/json'

    signature_string = authorization_header(
        access_key=server_access_key,
        secret_key=server_secret_key,
        method=method,
        content=content,
        content_type=content_type,
        date=date_string,
        request_path=request_path,
    )

    headers = {
        'Authorization': signature_string,
        'Date': date_string,
        'Content-Type': content_type,
    }

    url = urljoin(base=base_vws_url, url=request_path)

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        data=content,
    )

    return response


class VWS:
    """
    An interface to Vuforia Web Services APIs.
    """

    def __init__(
        self,
        server_access_key: str,
        server_secret_key: str,
        base_vws_url: str = 'https://vws.vuforia.com',
    ) -> None:
        """
        Args:
            server_access_key: A VWS server access key.
            server_secret_key: A VWS server secret key.
            base_vws_url: The base URL for the VWS API.
        """
        self._server_access_key = server_access_key
        self._server_secret_key = server_secret_key
        self._base_vws_url = base_vws_url

    def _make_request(
        self,
        method: str,
        content: bytes,
        request_path: str,
        expected_result_code: str,
    ) -> Response:
        """
        Make a request to the Vuforia Target API.

        This uses `requests` to make a request against https://vws.vuforia.com.
        The content type of the request will be `application/json`.

        Args:
            method: The HTTP method which will be used in the request.
            content: The request body which will be used in the request.
            request_path: The path to the endpoint which will be used in the
                request.
            expected_result_code: See
                https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Interperete-VWS-API-Result-Codes

        Returns:
            The response to the request made by `requests`.
        """
        response = _target_api_request(
            server_access_key=self._server_access_key,
            server_secret_key=self._server_secret_key,
            method=method,
            content=content,
            request_path=request_path,
            base_vws_url=self._base_vws_url,
        )

        raise_for_result_code(
            response=response,
            expected_result_code=expected_result_code,
        )

        return response

    def add_target(
        self,
        name: str,
        width: Union[int, float],
        image: io.BytesIO,
        active_flag: bool,
        application_metadata: Optional[str],
    ) -> str:
        """
        Add a target to a Vuforia Web Services database.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Add-a-Target
        for parameter details.

        Args:
            name: The name of the target.
            width: The width of the target.
            image: The image of the target.
            active_flag: Whether or not the target is active for query.
            application_metadata: The application metadata of the target.
                This must be base64 encoded, for example by using::

                    base64.b64encode('input_string').decode('ascii')

        Returns:
            The target ID of the new target.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.BadImage: There is a problem with the given image.
                For example, it must be a JPEG or PNG file in the grayscale or
                RGB color space.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.MetadataTooLarge: The given metadata is too large.
                The maximum size is 1 MB of data when Base64 encoded.
            ~vws.exceptions.ImageTooLarge: The given image is too large.
            ~vws.exceptions.TargetNameExist: A target with the given ``name``
                already exists.
            ~vws.exceptions.ProjectInactive: The project is inactive.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
            ~vws.exceptions.UnknownVWSErrorPossiblyBadName: Vuforia returns an
                HTML page with the text "Oops, an error occurred". This has
                been seen to happen when the given name includes a bad
                character.
        """
        image_data = image.getvalue()
        image_data_encoded = base64.b64encode(image_data).decode('ascii')

        data = {
            'name': name,
            'width': width,
            'image': image_data_encoded,
            'active_flag': active_flag,
            'application_metadata': application_metadata,
        }

        content = bytes(json.dumps(data), encoding='utf-8')

        response = self._make_request(
            method='POST',
            content=content,
            request_path='/targets',
            expected_result_code='TargetCreated',
        )

        return str(response.json()['target_id'])

    def get_target_record(self, target_id: str) -> TargetRecord:
        """
        Get a given target's target record from the Target Management System.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Retrieve-a-Target-Record.

        Args:
            target_id: The ID of the target to get details of.

        Returns:
            Response details of a target from Vuforia.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.UnknownTarget: The given target ID does not match a
                target in the database.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """
        response = self._make_request(
            method='GET',
            content=b'',
            request_path=f'/targets/{target_id}',
            expected_result_code='Success',
        )

        target_record_dict = dict(response.json()['target_record'])
        target_record = TargetRecord(
            target_id=target_record_dict['target_id'],
            active_flag=target_record_dict['active_flag'],
            name=target_record_dict['name'],
            width=target_record_dict['width'],
            tracking_rating=target_record_dict['tracking_rating'],
            reco_rating=target_record_dict['reco_rating'],
        )
        return target_record

    def _wait_for_target_processed(
        self,
        target_id: str,
        seconds_between_requests: float,
    ) -> None:
        """
        Wait indefinitely for a target to get past the processing stage.

        Args:
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
            report = self.get_target_summary_report(target_id=target_id)
            if report.status != TargetStatuses.PROCESSING:
                return

            sleep(seconds_between_requests)

    def wait_for_target_processed(
        self,
        target_id: str,
        seconds_between_requests: float = 0.2,
        timeout_seconds: Optional[float] = 60 * 5,
    ) -> None:
        """
        Wait up to five minutes (arbitrary) for a target to get past the
        processing stage.

        Args:
            target_id: The ID of the target to wait for.
            seconds_between_requests: The number of seconds to wait between
                requests made while polling the target status.
                We wait 0.2 seconds by default, rather than less, than that to
                decrease the number of calls made to the API, to decrease the
                likelihood of hitting the request quota.
            timeout_seconds: The maximum number of seconds to wait for the
                target to be processed. If ``None`` is given, no maximum is
                applied.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.TargetProcessingTimeout: The target remained in the
                processing stage for more than ``timeout_seconds`` seconds.
            ~vws.exceptions.UnknownTarget: The given target ID does not match a
                target in the database.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """

        @func_set_timeout(timeout=timeout_seconds)
        def decorated() -> None:
            self._wait_for_target_processed(
                target_id=target_id,
                seconds_between_requests=seconds_between_requests,
            )

        try:
            decorated()
        except FunctionTimedOut:
            raise TargetProcessingTimeout

    def list_targets(self) -> List[str]:
        """
        List target IDs.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Get-a-Target-List-for-a-Cloud-Database.

        Returns:
            The IDs of all targets in the database.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """
        response = self._make_request(
            method='GET',
            content=b'',
            request_path='/targets',
            expected_result_code='Success',
        )

        return list(response.json()['results'])

    def get_target_summary_report(self, target_id: str) -> TargetSummaryReport:
        """
        Get a summary report for a target.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Retrieve-a-Target-Summary-Report.

        Args:
            target_id: The ID of the target to get a summary report for.

        Returns:
            Details of the target.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.UnknownTarget: The given target ID does not match a
                target in the database.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """
        response = self._make_request(
            method='GET',
            content=b'',
            request_path=f'/summary/{target_id}',
            expected_result_code='Success',
        )

        result_data = dict(response.json())
        return TargetSummaryReport(
            status=TargetStatuses(result_data['status']),
            database_name=result_data['database_name'],
            target_name=result_data['target_name'],
            upload_date=date.fromisoformat(result_data['upload_date']),
            active_flag=result_data['active_flag'],
            tracking_rating=result_data['tracking_rating'],
            total_recos=result_data['total_recos'],
            current_month_recos=result_data['current_month_recos'],
            previous_month_recos=result_data['previous_month_recos'],
        )

    def get_database_summary_report(self) -> DatabaseSummaryReport:
        """
        Get a summary report for the database.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Get-a-Database-Summary-Report.

        Returns:
            Details of the database.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """
        response = self._make_request(
            method='GET',
            content=b'',
            request_path='/summary',
            expected_result_code='Success',
        )

        response_data = dict(response.json())
        database_summary_report = DatabaseSummaryReport(
            active_images=response_data['active_images'],
            current_month_recos=response_data['current_month_recos'],
            failed_images=response_data['failed_images'],
            inactive_images=response_data['inactive_images'],
            name=response_data['name'],
            previous_month_recos=response_data['previous_month_recos'],
            processing_images=response_data['processing_images'],
            reco_threshold=response_data['reco_threshold'],
            request_quota=response_data['request_quota'],
            request_usage=response_data['request_usage'],
            target_quota=response_data['target_quota'],
            total_recos=response_data['total_recos'],
        )
        return database_summary_report

    def delete_target(self, target_id: str) -> None:
        """
        Delete a given target.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Delete-a-Target.

        Args:
            target_id: The ID of the target to delete.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.UnknownTarget: The given target ID does not match a
                target in the database.
            ~vws.exceptions.TargetStatusProcessing: The given target is in the
                processing state.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """
        self._make_request(
            method='DELETE',
            content=b'',
            request_path=f'/targets/{target_id}',
            expected_result_code='Success',
        )

    def get_duplicate_targets(self, target_id: str) -> List[str]:
        """
        Get targets which may be considered duplicates of a given target.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Check-for-Duplicate-Targets.

        Args:
            target_id: The ID of the target to delete.

        Returns:
            The target IDs of duplicate targets.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.UnknownTarget: The given target ID does not match a
                target in the database.
            ~vws.exceptions.ProjectInactive: The project is inactive.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """
        response = self._make_request(
            method='GET',
            content=b'',
            request_path=f'/duplicates/{target_id}',
            expected_result_code='Success',
        )

        return list(response.json()['similar_targets'])

    def update_target(
        self,
        target_id: str,
        name: Optional[str] = None,
        width: Optional[Union[int, float]] = None,
        image: Optional[io.BytesIO] = None,
        active_flag: Optional[bool] = None,
        application_metadata: Optional[str] = None,
    ) -> None:
        """
        Add a target to a Vuforia Web Services database.

        See
        https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API#How-To-Add-a-Target
        for parameter details.

        Args:
            target_id: The ID of the target to get details of.
            name: The name of the target.
            width: The width of the target.
            image: The image of the target.
            active_flag: Whether or not the target is active for query.
            application_metadata: The application metadata of the target.
                This must be base64 encoded, for example by using::

                    base64.b64encode('input_string').decode('ascii')

                Giving ``None`` will not change the application metadata.

        Raises:
            ~vws.exceptions.AuthenticationFailure: The secret key is not
                correct.
            ~vws.exceptions.BadImage: There is a problem with the given image.
                For example, it must be a JPEG or PNG file in the grayscale or
                RGB color space.
            ~vws.exceptions.Fail: There was an error with the request. For
                example, the given access key does not match a known database.
            ~vws.exceptions.MetadataTooLarge: The given metadata is too large.
                The maximum size is 1 MB of data when Base64 encoded.
            ~vws.exceptions.ImageTooLarge: The given image is too large.
            ~vws.exceptions.TargetNameExist: A target with the given ``name``
                already exists.
            ~vws.exceptions.ProjectInactive: The project is inactive.
            ~vws.exceptions.RequestTimeTooSkewed: There is an error with the
                time sent to Vuforia.
        """
        data: Dict[str, Union[str, bool, float, int]] = {}

        if name is not None:
            data['name'] = name

        if width is not None:
            data['width'] = width

        if image is not None:
            image_data = image.getvalue()
            image_data_encoded = base64.b64encode(image_data).decode('ascii')
            data['image'] = image_data_encoded

        if active_flag is not None:
            data['active_flag'] = active_flag

        if application_metadata is not None:
            data['application_metadata'] = application_metadata

        content = bytes(json.dumps(data), encoding='utf-8')

        self._make_request(
            method='PUT',
            content=content,
            request_path=f'/targets/{target_id}',
            expected_result_code='Success',
        )
