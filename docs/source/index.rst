|project|
=========

Installation
------------

.. code-block:: console

   $ pip install vws-python

This is tested on Python |minimum-python-version|\+.
Get in touch with ``adamdangoor@gmail.com`` if you would like to use this with another language.

Usage
-----

See the :doc:`api-reference` for full usage details.

.. code-block:: python

   """Add a target to VWS and then query it."""

   import os
   import pathlib
   import uuid

   from vws import VWS, CloudRecoService

   server_access_key = os.environ["VWS_SERVER_ACCESS_KEY"]
   server_secret_key = os.environ["VWS_SERVER_SECRET_KEY"]
   client_access_key = os.environ["VWS_CLIENT_ACCESS_KEY"]
   client_secret_key = os.environ["VWS_CLIENT_SECRET_KEY"]

   vws_client = VWS(
       server_access_key=server_access_key,
       server_secret_key=server_secret_key,
   )

   cloud_reco_client = CloudRecoService(
       client_access_key=client_access_key,
       client_secret_key=client_secret_key,
   )

   name = "my_image_name_" + uuid.uuid4().hex

   image = pathlib.Path("high_quality_image.jpg")
   with image.open(mode="rb") as my_image_file:
       target_id = vws_client.add_target(
           name=name,
           width=1,
           image=my_image_file,
           active_flag=True,
           application_metadata=None,
       )

   vws_client.wait_for_target_processed(target_id=target_id)

   with image.open(mode="rb") as my_image_file:
       matching_targets = cloud_reco_client.query(image=my_image_file)

   assert matching_targets[0].target_id == target_id

Recognition counts
------------------

Vuforia can generate a report of the number of recognitions of each target in a database in a month.
Only the current month and the previous month can be requested.

This needs the ID of the database, which is shown in the Vuforia target manager.

The report is generated in the background, and the URL it is served from expires just under seven days after it is requested.

.. clear-namespace

.. code-block:: python

   """Get the number of recognitions of each target this month."""

   import datetime
   import os

   from vws import VWS

   server_access_key = os.environ["VWS_SERVER_ACCESS_KEY"]
   server_secret_key = os.environ["VWS_SERVER_SECRET_KEY"]
   database_id = os.environ["VWS_DATABASE_ID"]

   vws_client = VWS(
       server_access_key=server_access_key,
       server_secret_key=server_secret_key,
       database_id=database_id,
   )

   now = datetime.datetime.now(tz=datetime.UTC)

   report_request = vws_client.request_database_reco_counts_report(
       year=now.year,
       month=now.month,
   )

   report = vws_client.wait_for_reco_counts_report(
       presigned_url=report_request.presigned_url,
   )

   reco_counts_by_target_id = {
       item.target_id: item.reco_count for item in report.reco_counts
   }

   # This database has no targets, so nothing has been recognized.
   assert not reco_counts_by_target_id

Testing
-------

To write unit tests for code which uses this library, without using your Vuforia quota, you can use the `VWS Python Mock`_ tool:

.. code-block:: console

   $ pip install vws-python-mock

.. clear-namespace

.. code-block:: python

    """Add a target to VWS and then query it."""

    import pathlib

    from mock_vws import MockVWS
    from mock_vws.database import CloudDatabase

    from vws import VWS, CloudRecoService

    with MockVWS() as mock:
        database = CloudDatabase()
        mock.add_cloud_database(cloud_database=database)
        vws_client = VWS(
            server_access_key=database.server_access_key,
            server_secret_key=database.server_secret_key,
        )
        cloud_reco_client = CloudRecoService(
            client_access_key=database.client_access_key,
            client_secret_key=database.client_secret_key,
        )

        image = pathlib.Path("high_quality_image.jpg")
        with image.open(mode="rb") as my_image_file:
            target_id = vws_client.add_target(
                name="example_image_name",
                width=1,
                image=my_image_file,
                application_metadata=None,
                active_flag=True,
            )

            vws_client.wait_for_target_processed(target_id=target_id)
            matching_targets = cloud_reco_client.query(image=my_image_file)

        assert matching_targets[0].target_id == target_id

There are some differences between the mock and the real Vuforia.
See https://vws-python.github.io/vws-python-mock/differences-to-vws for details.

.. _VWS Python Mock: https://github.com/VWS-Python/vws-python-mock

Reference
---------

.. toctree::
   :maxdepth: 3

   api-reference
   exceptions
   contributing
   release-process
   unreleased
   changelog
