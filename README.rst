|Build Status| |codecov| |Updates| |PyPI| |Documentation Status|

vws-python
==========

Python library for the Vuforia Web Services (VWS) API and the Vuforia Web Query API.

Installation
------------

.. code:: sh

   pip install vws-python

This is tested on Python 3.7+.
Get in touch with ``adamdangoor@gmail.com`` if you would like to use this with another language.

Getting Started
---------------

.. code:: python

   import io

   from vws import VWS, CloudRecoService

   vws_client = VWS(server_access_key='...', server_secret_key='...')
   cloud_reco_client = CloudRecoService(client_access_key='...', client_secret_key='...')
   name = 'my_image_name'

   with open('/path/to/image.png', 'rb') as my_image_file:
      my_image = io.BytesIO(my_image_file.read())

   target_id = vws_client.add_target(
       name=name,
       width=1,
       image=my_image,
   )
   vws_client.wait_for_target_processed(target_id=target_id)
   matching_targets = cloud_reco_client.query(image=my_image)

   assert matching_targets[0]['target_id'] == target_id


Full Documentation
------------------

See the `full documentation <https://vws-python.readthedocs.io/en/latest>`__.

.. |Build Status| image:: https://travis-ci.org/adamtheturtle/vws-python.svg?branch=master
   :target: https://travis-ci.org/adamtheturtle/vws-python
.. |codecov| image:: https://codecov.io/gh/adamtheturtle/vws-python/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/adamtheturtle/vws-python
.. |Updates| image:: https://pyup.io/repos/github/adamtheturtle/vws-python/shield.svg
   :target: https://pyup.io/repos/github/adamtheturtle/vws-python/
.. |Documentation Status| image:: https://readthedocs.org/projects/vws-python/badge/?version=latest
   :target: https://vws-python.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. |PyPI| image:: https://badge.fury.io/py/VWS-Python.svg
   :target: https://badge.fury.io/py/VWS-Python
