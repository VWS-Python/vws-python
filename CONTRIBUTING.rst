Contributing to VWS Python
==========================

.. contents::

Contributions to this repository must pass tests and linting.

Travis CI is the canonical source truth.

Install Contribution Dependencies
---------------------------------

Install Python dependencies in a virtual environment.

.. code:: sh

    pip install --editable .[dev]

Spell checking requires ``enchant``.
This can be installed on macOS, for example, with `Homebrew <http://brew.sh>`__:

.. code:: sh

    brew install enchant

and on Ubuntu with ``apt``:

.. code:: sh

    apt-get install -y enchant

Linting
-------

Run lint tools:

.. code:: sh

    make lint

To fix some lint errors, run the following:

.. code:: sh

    make fix-lint

Running tests
-------------

Run ``pytest``:

.. code:: sh

    pytest

Documentation
-------------

Documentation is built on Read the Docs.

Run the following commands to build and view documentation locally:

.. code:: sh

   make docs
   make open-docs

Travis CI
---------

Tests are run on Travis CI.
The configuration for this is in ``.travis.yml``.

Performing a release
--------------------

See release process in the full documentation.
