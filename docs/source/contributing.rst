Contributing to |project|
=========================

Contributions to this repository must pass tests and linting.

CI is the canonical source of truth.

Install contribution dependencies
---------------------------------

Install Python dependencies in a virtual environment.

.. prompt:: bash

   pip install --editable '.[dev]'

Spell checking requires ``enchant``.
This can be installed on macOS, for example, with `Homebrew <https://brew.sh>`__:

.. prompt:: bash

   brew install enchant

and on Ubuntu with ``apt``:

.. prompt:: bash

   apt-get install -y enchant

Linting
-------

Run lint tools:

.. prompt:: bash

   make lint

To fix some lint errors, run the following:

.. prompt:: bash

   make fix-lint

Running tests
-------------

Run ``pytest``:

.. prompt:: bash

   pytest

Documentation
-------------

Documentation is built on Read the Docs.

Run the following commands to build and view documentation locally:

.. prompt:: bash

   make docs
   make open-docs

Continuous integration
----------------------

Tests are run on GitHub Actions.
The configuration for this is in :file:`.github/workflows/`.

Performing a release
--------------------

See :doc:`release-process`.
