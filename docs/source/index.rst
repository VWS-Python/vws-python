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

.. testsetup:: simple

   import pathlib
   import shutil

   import vws_test_fixtures
   from mock_vws import MockVWS
   from mock_vws.database import VuforiaDatabase

   mock = MockVWS(real_http=False)
   database = VuforiaDatabase(
       server_access_key='[server-access-key]',
       server_secret_key='[server-secret-key]',
       client_access_key='[client-access-key]',
       client_secret_key='[client-secret-key]',
   )
   mock.add_database(database=database)
   mock.__enter__()

   # We rely on implementation details of the fixtures package.
   image = pathlib.Path(vws_test_fixtures.__path__[0]) / 'high_quality_image.jpg'
   assert image.exists(), image.resolve()
   new_image = pathlib.Path('high_quality_image.jpg')
   shutil.copy(image, new_image)

.. testcode:: simple

   import io
   import pathlib

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

   image = pathlib.Path('high_quality_image.jpg')
   with image.open(mode='rb') as my_image_file:
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

.. testcleanup:: simple

   new_image = pathlib.Path('high_quality_image.jpg')
   new_image.unlink()
   mock.__exit__()

Testing
-------

To write unit tests for code which uses this library, without using your Vuforia quota, you can use the `VWS Python Mock`_ tool:

.. prompt:: bash

   pip3 install vws-python-mock

.. testsetup:: testing

   import pathlib
   import shutil

   import vws_test_fixtures

   # We rely on implementation details of the fixtures package.
   image = pathlib.Path(vws_test_fixtures.__path__[0]) / 'high_quality_image.jpg'
   assert image.exists(), image.resolve()
   new_image = pathlib.Path('high_quality_image.jpg')
   shutil.copy(image, new_image)

.. testcode:: testing

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


       image = pathlib.Path('high_quality_image.jpg')
       with image.open(mode='rb') as my_image_file:
           my_image = io.BytesIO(my_image_file.read())

       target_id = vws_client.add_target(
           name="example_image_name",
           width=1,
           image=my_image,
           application_metadata=None,
           active_flag=True,
       )

.. testcleanup:: testing

   new_image = pathlib.Path('high_quality_image.jpg')
   new_image.unlink()

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
