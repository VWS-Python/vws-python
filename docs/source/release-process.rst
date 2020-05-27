Release Process
===============

Outcomes
~~~~~~~~

* A new ``git`` tag available to install.
* A new package on PyPI.

Prerequisites
~~~~~~~~~~~~~

* ``python3`` on your ``PATH`` set to Python 3.8+.
* ``virtualenv``.
* Push access to this repository.
* Trust that ``master`` is ready and high enough quality for release.

Perform a Release
~~~~~~~~~~~~~~~~~

#. Install keyring

   Make sure that `keyring <https://pypi.org/project/keyring/>`__ is available on your path.

   E.g.:

   .. prompt:: bash

      python3 -m pip install --user pipx
      python3 -m pipx ensurepath
      pipx install keyring

#. Set up PyPI credentials

Register at `PyPI <https://pypi.org>`__.

Add the following information to :file:`~/.pypirc`.

.. code:: ini

   [distutils]
    index-servers=
        pypi

    [pypi]
    username = <Your PyPI username>

Store your PyPI password:

.. prompt:: bash

   keyring set https://upload.pypi.org/legacy/ <Your PyPI username>

#. Get a GitHub access token:

   Follow the `GitHub access token instructions`_ for getting an access token.

#. Set environment variables to GitHub credentials, e.g.:

    .. prompt:: bash

       export GITHUB_TOKEN=75c72ad718d9c346c13d30ce762f121647b502414

#. Perform a release:

   .. prompt:: bash
      :substitutions:

      export GITHUB_OWNER=|github-owner|
      export GITHUB_REPOSITORY_NAME=|github-repository|
      curl https://raw.githubusercontent.com/"$GITHUB_OWNER"/"$GITHUB_REPOSITORY_NAME"/master/admin/release.sh | bash

.. _GitHub access token instructions: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line/
