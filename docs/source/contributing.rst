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
This can be installed on macOS, for example, with `Homebrew`_:

.. prompt:: bash

   brew install enchant

and on Ubuntu with ``apt``:

.. prompt:: bash

   apt-get install -y enchant

Install ``pre-commit`` hooks:

.. prompt:: bash

   pre-commit install

Linting
-------

Run lint tools either by committing, or with:

.. prompt:: bash

   pre-commit run --all-files --hook-stage commit --verbose
   pre-commit run --all-files --hook-stage push --verbose
   pre-commit run --all-files --hook-stage manual --verbose

.. _Homebrew: https://brew.sh

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
