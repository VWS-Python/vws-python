|project|
=========

Installation
------------

.. prompt:: bash

   pip3 install vws-python

This is tested on Python 3.8+.
Get in touch with ``adamdangoor@gmail.com`` if you would like to use this with another language.

Usage
-----

See the :doc:`api-reference` for full usage details.

.. TODO - make this a doctest with hidden mock as setup

.. code:: python

   import io

   from vws import VWS, CloudRecoService

   server_access_key = '[server-access-key]'
   server_secret_key = '[server-secret-key]'
   client_access_key = '[client-access-key]'
   client_secret_key = '[client-secret-key]'

   vws_client = VWS(
       server_access_key=server_access_key,
       server_secret_key=server_secret_key,
   )
   cloud_reco_client = CloudRecoService(
       client_access_key=client_access_key,
       client_secret_key=client_secret_key,
   )
   name = 'my_image_name'

   with open('/path/to/image.png', 'rb') as my_image_file:
      my_image = io.BytesIO(my_image_file.read())

   target_id = vws_client.add_target(
       name=name,
       width=1,
       image=my_image,
       active_flag=True,
       application_metadata=None,
   )
   vws_client.wait_for_target_processed(target_id=target_id)
   matching_targets = cloud_reco_client.query(image=my_image)

   assert matching_targets[0].target_id == target_id

Testing
-------

To write unit tests for code which uses this library, without using your Vuforia quota, you can use the `VWS Python Mock`_ tool:

.. prompt:: bash

   pip3 install vws-python-mock

.. testcode::

   import io
   import pathlib

   from mock_vws.database import VuforiaDatabase
   from mock_vws import MockVWS
   from vws import CloudRecoService, VWS

   with MockVWS() as mock:
       database = VuforiaDatabase()
       mock.add_database(database=database)
       vws_client = VWS(
           server_access_key=database.server_access_key,
           server_secret_key=database.server_secret_key,
       )
       cloud_reco_client = CloudRecoService(
           client_access_key=database.client_access_key,
           client_secret_key=database.client_secret_key,
       )


       image = pathlib.Path('high_quality_image.jpg').resolve()
       with image.open(mode='rb') as my_image_file:
           my_image = io.BytesIO(my_image_file.read())

       target_id = vws_client.add_target(
           name="example_image_name",
           width=1,
           image=my_image,
           application_metadata=None,
           active_flag=True,
       )

There are some differences between the mock and the real Vuforia.
See https://vws-python-mock.readthedocs.io/en/latest/differences-to-vws.html for details.

.. _VWS Python Mock: https://github.com/VWS-Python/vws-python-mock


Reference
---------

.. toctree::
   :maxdepth: 3

   api-reference
   exceptions
   contributing
   release-process
   changelog
