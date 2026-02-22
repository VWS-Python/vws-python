Changelog
=========

Next
----

2026.02.22
----------


2026.02.21
----------


2026.02.15
----------


* Add ``request_timeout_seconds`` parameter to ``VWS`` and ``CloudRecoService``, allowing customization of the request timeout. This accepts a float or a ``(connect, read)`` tuple, matching the ``requests`` library's timeout interface. The default remains 30 seconds.

2025.03.10.1
------------

2025.03.10
----------

* Removed ``vws.exceptions.custom_exceptions.OopsAnErrorOccurredPossiblyBadName`` which now does not occur in VWS.

2024.09.21
------------

2024.09.04.1
------------

2024.09.04
------------

* Move ``Response`` from ``vws.exceptions.response`` to ``vws.types``.
* Add ``raw`` field to ``Response``.

2024.09.03
------------

* Make ``VWS.make_request`` a public method.

2024.09.02
------------

* Breaking change: Exception names now end with ``Error``.
* Use a timeout (30 seconds) when making requests to the VWS API.
* Type hint changes: images are now ``io.BytesIO`` instances or ``io.BufferedRandom``.

2024.02.19
------------

* Add exception response attribute to ``vws.exceptions.custom_exceptions.RequestEntityTooLarge``.

2024.02.06
------------

* Exception response attributes are now ``vws.exceptions.response.Response`` instances rather than ``requests.Response`` objects.

2024.02.04.1
------------

2024.02.04
------------

* Return a new error (``vws.custom_exceptions.ServerError``) when the server returns a 5xx status code.

2023.12.27
------------

* Breaking change: The ``vws.exceptions.cloud_reco_exceptions.UnknownVWSErrorPossiblyBadName`` is now ``vws.exceptions.custom_exceptions.OopsAnErrorOccurredPossiblyBadName``.
* ``vws.exceptions.custom_exceptions.OopsAnErrorOccurredPossiblyBadName`` now has a ``response`` parameter and attribute.

2023.12.26
------------

2023.05.21
------------

* Breaking change: the ``vws.exceptions.custom_exceptions.ActiveMatchingTargetsDeleteProcessing`` exception has been removed as Vuforia no longer returns this error.

2023.03.25
------------

* Support file-like objects in every method which accepts a file.

2023.03.05
------------

2021.03.28.2
------------

2021.03.28.1
------------

2021.03.28.0
------------

* Breaking change: The ``vws.exceptions.cloud_reco_exceptions.MatchProcessing`` is now ``vws.exceptions.custom_exceptions.ActiveMatchingTargetsDeleteProcessing``.
* Added new exception ``vws.exceptions.custom_exceptions.RequestEntityTooLarge``.
* Add better exception handling when querying a server which does not serve the Vuforia API.

2020.09.07.0
------------

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
