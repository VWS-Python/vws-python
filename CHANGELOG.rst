Changelog
=========

.. contents::

Next
----

* Breaking change: Move exceptions and create base exceptions.
  It is now possible to, for example, catch
  ``vws.exceptions.base_exceptions.VWSException`` to catch many of the
  exceptions raised by the ``VWS`` client.
  Credit to ``@laymonage`` for this change.

2020.08.21.0
------------

* Change the return type of ``vws_client.get_target_record`` to match what is returned by the web API.

2020.06.19.0
------------

2020.03.21.0
------------

* Add Windows support.

2019.11.23.0
------------

* Make ``active_flag`` and ``application_metadata`` required on ``add_target``.
