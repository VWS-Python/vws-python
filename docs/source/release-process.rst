Release Process
===============

Outcomes
~~~~~~~~

* A new ``git`` tag available to install.
* A new package on PyPI.

Prerequisites
~~~~~~~~~~~~~

* ``python3`` on your ``PATH`` set to Python 3.9+.
* ``virtualenv``.
* Push access to this repository.
* Trust that ``master`` is ready and high enough quality for release.

Perform a Release
~~~~~~~~~~~~~~~~~

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
