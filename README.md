[![Build Status](https://travis-ci.org/adamtheturtle/vws-python.svg?branch=master)](https://travis-ci.com/adamtheturtle/vws-python)
[![Coverage Status](https://coveralls.io/repos/github/adamtheturtle/vws-python/badge.svg)](https://coveralls.io/github/adamtheturtle/vws-python)
[![Code Health](https://landscape.io/github/adamtheturtle/vws-python/master/landscape.svg?style=flat)](https://landscape.io/github/adamtheturtle/vws-python/master)


# vws-python
Python wrapper for Vuforia Web Services (VWS) API

# Tests

To run the tests, first install the dependencies:

    pip install -e .[dev]

Then run `pytest`:

    pytest

# Connecting to Vuforia

Set the `VWS_LICENSE` environment variable.

For integration which use Vuforia tests, create a file `vuforia_secrets.env` with the format:

    VWS_LICENSE=<APPLICATION_LICENSE_KEY> 
