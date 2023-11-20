|Build Status| |codecov| |PyPI| |Documentation Status|

vws-python
==========

Python library for the Vuforia Web Services (VWS) API and the Vuforia
Web Query API.

Installation
------------

.. code:: sh

   pip install vws-python

This is tested on Python 3.12+. Get in touch with
``adamdangoor@gmail.com`` if you would like to use this with another
language.

Getting Started
---------------

.. invisible-code-block: python

   import contextlib
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
   stack = contextlib.ExitStack()
   stack.enter_context(mock)

   # We rely on implementation details of the fixtures package.
   image = pathlib.Path(vws_test_fixtures.__path__[0]) / 'high_quality_image.jpg'
   assert image.exists(), image.resolve()
   new_image = pathlib.Path('high_quality_image.jpg')
   shutil.copy(image, new_image)


.. code-block:: python

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
       target_id = vws_client.add_target(
           name=name,
           width=1,
           image=my_image_file,
           active_flag=True,
           application_metadata=None,
       )
       vws_client.wait_for_target_processed(target_id=target_id)
       matching_targets = cloud_reco_client.query(image=my_image_file)

   assert matching_targets[0].target_id == target_id

.. invisible-code-block: python
   new_image = pathlib.Path('high_quality_image.jpg')
   new_image.unlink()
   stack.close()

Full Documentation
------------------

See the `full
documentation <https://vws-python.readthedocs.io/en/latest>`__.

.. |Build Status| image:: https://github.com/VWS-Python/vws-python/workflows/CI/badge.svg
   :target: https://github.com/VWS-Python/vws-python/actions
.. |codecov| image:: https://codecov.io/gh/VWS-Python/vws-python/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/VWS-Python/vws-python
.. |PyPI| image:: https://badge.fury.io/py/VWS-Python.svg
   :target: https://badge.fury.io/py/VWS-Python
.. |Documentation Status| image:: https://readthedocs.org/projects/vws-python/badge/?version=latest
   :target: https://vws-python.readthedocs.io/en/latest/?badge=latest
