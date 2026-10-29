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

   """Generate a VuMark instance."""

   import os

   from vws import VuMarkService
   from vws.vumark_accept import VuMarkAccept

   client = VuMarkService(
       server_access_key=os.environ["VWS_SERVER_ACCESS_KEY"],
       server_secret_key=os.environ["VWS_SERVER_SECRET_KEY"],
   )
   image = client.generate_vumark_instance(
       target_id=os.environ["VUMARK_TARGET_ID"],
       instance_id="123",
       accept=VuMarkAccept.PNG,
   )
   assert image.startswith(b"\x89PNG")

Model Targets
-------------

Vuforia generates Model Target datasets from CAD models.
This uses OAuth2 client credentials, which are separate from the VWS server keys.

Dataset generation happens in the background, and the generated dataset is downloaded as a zip file.

.. clear-namespace

.. code-block:: python

   """Generate a Model Target dataset and download it."""

   import os

   from vws import ModelTargetService
   from vws.model_target_datasets import (
       CadDataFormat,
       GuideViewPosition,
       ModelTargetDatasetType,
       ModelTargetModel,
       ModelTargetView,
   )
   from vws.reports import ModelTargetDatasetStatuses

   client_id = os.environ["VWS_MODEL_TARGET_CLIENT_ID"]
   client_secret = os.environ["VWS_MODEL_TARGET_CLIENT_SECRET"]

   model_target_client = ModelTargetService(
       client_id=client_id,
       client_secret=client_secret,
   )

   model = ModelTargetModel(
       name="my_model",
       cad_data_url="https://example.com/my_model.zip",
       cad_data_format=CadDataFormat.ZIP,
       views=[
           ModelTargetView(
               name="front",
               guide_view_position=GuideViewPosition(
                   rotation=[0.0, 0.0, 0.0, 1.0],
                   translation=[0.0, 0.0, 1.0],
               ),
           ),
       ],
   )

   dataset_uuid = model_target_client.create_dataset(
       name="my_dataset",
       target_sdk="11.0",
       models=[model],
       dataset_type=ModelTargetDatasetType.STANDARD,
   )

   report = model_target_client.wait_for_dataset_generated(
       dataset_uuid=dataset_uuid,
       dataset_type=ModelTargetDatasetType.STANDARD,
   )

   assert report.status == ModelTargetDatasetStatuses.DONE

   dataset = model_target_client.download_dataset(
       dataset_uuid=dataset_uuid,
       dataset_type=ModelTargetDatasetType.STANDARD,
   )

   # The dataset is a zip file.
   assert dataset.startswith(b"PK")

   model_target_client.delete_dataset(
       dataset_uuid=dataset_uuid,
       dataset_type=ModelTargetDatasetType.STANDARD,
   )

HTTP transports
---------------

By default, the synchronous clients make requests with `requests`_ and the asynchronous clients make requests with `httpx`_.
To use another HTTP library, pass a transport from :mod:`vws.transports` to a client.

Transports are available for `requests`_, `httpx`_ and `HTTPX2`_.
``httpx`` and ``httpx2`` are separate packages with separate client, response and exception classes.
``HTTPXTransport`` and ``AsyncHTTPXTransport`` use ``httpx`` and raise ``httpx`` exceptions.
``HTTPX2Transport`` and ``AsyncHTTPX2Transport`` use ``httpx2`` and raise ``httpx2`` exceptions.

.. clear-namespace

.. _requests: https://pypi.org/project/requests/
.. _httpx: https://pypi.org/project/httpx/
.. _HTTPX2: https://httpx2.pydantic.dev/

Testing
-------

Use `VWS Python Mock <https://github.com/VWS-Python/vws-python-mock>`_ to test Model Target and VuMark clients without calling Vuforia.

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
