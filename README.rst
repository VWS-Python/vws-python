|Build Status| |PyPI|

vws-python
==========

Python clients for the Vuforia Model Target Web API and VuMark generation.

Installation
------------

.. code-block:: shell

   pip install vws-python

This is tested on Python |minimum-python-version|\+.
Get in touch with ``adamdangoor@gmail.com`` if you would like to use this with another language.

Getting Started
---------------

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

Full Documentation
------------------

See the `full documentation <https://vws-python.github.io/vws-python/>`__.

.. |Build Status| image:: https://github.com/VWS-Python/vws-python/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/VWS-Python/vws-python/actions
.. |PyPI| image:: https://badge.fury.io/py/VWS-Python.svg
   :target: https://badge.fury.io/py/VWS-Python
.. |minimum-python-version| replace:: 3.14
