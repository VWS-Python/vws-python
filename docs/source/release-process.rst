Release Process
===============

Outcomes
~~~~~~~~

* A new ``git`` tag available to install.
* A new package on PyPI.

Perform a Release
~~~~~~~~~~~~~~~~~

#. `Install GitHub CLI`_.

#. Perform a release:

   .. prompt:: bash
      :substitutions:

      gh workflow run release.yml --repo |github-owner|/|github-repository|

.. _Install GitHub CLI: https://cli.github.com/
