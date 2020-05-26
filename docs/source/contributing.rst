Contributing to |project|
=========================

.. contents::

Contributions to this repository must pass tests and linting.

Travis CI is the canonical source of truth.

Install contribution dependencies
---------------------------------

Install Python dependencies in a virtual environment.

.. substitution-prompt:: bash

    pip install --editable '.[dev]'

Spell checking requires ``enchant``.
This can be installed on macOS, for example, with `Homebrew <https://brew.sh>`__:

.. substitution-prompt:: bash

    brew install enchant

and on Ubuntu with ``apt``:

.. substitution-prompt:: bash

    apt-get install -y enchant

Linting
-------

Run lint tools:

.. substitution-prompt:: bash

    make lint

To fix some lint errors, run the following:

.. substitution-prompt:: bash

    make fix-lint

Running tests
-------------

Run ``pytest``:

.. substitution-prompt:: bash

    pytest

Documentation
-------------

Documentation is built on Read the Docs.

Run the following commands to build and view documentation locally:

.. substitution-prompt:: bash

   make docs
   make open-docs

Travis CI
---------

Tests are run on Travis CI.
The configuration for this is in :file:`.travis.yml`.

Performing a release
--------------------

See :doc:`release-process`.
