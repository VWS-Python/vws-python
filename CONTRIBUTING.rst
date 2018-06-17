Contributing to VWS Python Mock
===============================

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

Create an environment variable file for secrets:

.. code:: sh

    cp vuforia_secrets.env.example vuforia_secrets.env

Some tests require Vuforia credentials.
To run these tests, add the Vuforia credentials to the file ``vuforia_secrets.env``.
See “Connecting to Vuforia”.

Then run ``pytest``:

.. code:: sh

    pytest

Connecting to Vuforia
---------------------

To connect to Vuforia, Vuforia target databases must be created via the Vuforia Web UI.
Then, secret keys must be set as environment variables.

The test infrastructure allows those keys to be set in the file ``vuforia_secrets.env``.
See ``vuforia_secrets.env.example`` for the environment variables to set.

Do not use a target database that you are using for other purposes.
This is because the test suite adds and deletes targets.

To create a target database, first create a license key in the `License Manager <https://developer.vuforia.com/targetmanager/licenseManager/licenseListing>`__.
Then, add a database from the `Target Manager <https://developer.vuforia.com/targetmanager>`__.

To find the environment variables to set in the ``vuforia_secrets.env`` file, visit the Target Database in the Target Manager and view the “Database Access Keys”.

Two databases are necessary in order to run all the tests.
One of those must be an inactive project.
To create an inactive project, delete the license key associated with a database.

Targets sometimes get stuck at the “Processing” stage meaning that they cannot be deleted.
When this happens, create a new target database to use for testing.

Skipping some tests
-------------------

Set either ``SKIP_MOCK`` or ``SKIP_REAL`` to ``1`` to skip tests against the mock, or tests against the real implementation, for tests which run against both.

Travis CI
---------

Tests are run on Travis CI.
The configuration for this is in ``.travis.yml``.

Travis CI is set up with secrets for connecting to Vuforia.
These variables include those from ``vuforia_secrets.env.example``.

To avoid hitting request quotas and to avoid conflicts when running multiple tests in prallel, we use multiple target databases.

Travis builds use a different credentials file depending on the build number.
For example, build 2045.1 will use a different credentials file to build 2045.2.
This should avoid conflicts, but in theory the same credentials file may be run across two Pull Request builds.
This may cause errors.

How to set Travis CI secrets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create environment variable files for secrets:

.. code:: sh

    mkdir -p ci_secrets
    cp vuforia_secrets.env.example ci_secrets/vuforia_secrets_1.env
    cp vuforia_secrets.env.example ci_secrets/vuforia_secrets_2.env
    ...

Add Vuforia credentials for different target databases to the new files in the ``ci_secrets/`` directory.
Add as many credentials files as there are builds in the Travis matrix.
All credentials files can share the same credentials for an inactive database.

Install the Travis CLI:

.. code:: sh

    gem install travis --no-rdoc --no-ri

Add the encrypted secrets files to the repository and Travis CI:

.. code:: sh

    make update-secrets

Note that the `Travis CI documentation <https://docs.travis-ci.com/user/encrypting-files/#Caveat>`__ warns that this might not work on Windows.

Travis CI Settings
~~~~~~~~~~~~~~~~~~

All targets are deleted from the database between each test.
Therefore there may be conflicts if the test suite is run concurrently as Travis CI is configured to connect to one Vuforia database.
As such, Travis CI is configured not to run multiple instances of the test suite concurrently.

Learnings about VWS
-------------------

Vuforia Web Services, at the time of writing, does not behave exactly as documented.

The following list includes details of differences between VWS and expected or documented behaviour.

When attempting to delete a target immediately after creating it, a ``FORBIDDEN`` response is returned.
This is because the target goes into a processing state.

``image`` is required for ``POST /targets``, but it is documented as not mandatory.

The ``tracking_rating`` returned by ``GET /targets/<target_id>`` can be -1.

The database summary from ``GET /summary`` has multiple undocumented return fields.

The database summary from ``GET /summary`` has is not immediately accurate.

Some of the `Vuforia Web Services documentation <https://library.vuforia.com/articles/Training/Image-Target-Guide>`__ states that “The size of the input images must 2 MB or less”.
However, other `Vuforia Web Services documentation <https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query>`__ is more accurate: “Maximum image size: 2.1 MPixel.
512 KiB for JPEG, 2MiB for PNG”.

The documentation page `How To Perform an Image Recognition Query <https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query>`__ states that the ``Content-Type`` header must be set to ``multipart/form-data``.
However, it must be set to ``multipart/form-data; boundary=<BOUNDARY>`` where ``<BOUNDARY>`` is the boundary used when encoding the form data.

The documentation page `How To Perform an Image Recognition Query <https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query>`__ states that ``Content-Type`` will be the only response header.
This is not the case.

The documentation page `How To Perform an Image Recognition Query <https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query>`__ states that 10 is the maximum allowed value of ``max_num_results``.
However, the maximum allowed value is 50.

A response to an invalid query may have an ``application/json`` content type but include text (not JSON) data.

After deleting a target, for up to approximately 30 seconds, matching it with a query returns a 500 response.

A target with the name ``\uffff`` gets stuck in processing.

The documentation page `How To Perform an Image Recognition Query`_ states that "The API accepts requests with unknown data fields, and ignore the unknown fields.".
This is not the case.

The documentation page `How To Perform an Image Recognition Query <query-article>`__ states "Maximum image size: 2.1 MPixel. 512 KiB for JPEG, 2MiB for PNG".
However, JPEG images up to 2MiB are accepted.

.. _How To Perform an Image Recognition Query: https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query

Performing a release
--------------------

There is currently no release process.
See `this issue <https://github.com/adamtheturtle/vws-python/issues/55>`__ for details.
