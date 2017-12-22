[![Build Status](https://travis-ci.org/adamtheturtle/vws-python.svg?branch=master)](https://travis-ci.org/adamtheturtle/vws-python)
[![codecov](https://codecov.io/gh/adamtheturtle/vws-python/branch/master/graph/badge.svg)](https://codecov.io/gh/adamtheturtle/vws-python)
[![Requirements Status](https://requires.io/github/adamtheturtle/vws-python/requirements.svg?branch=master)](https://requires.io/github/adamtheturtle/vws-python/requirements/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/vws-python/badge/?version=latest)](http://vws-python.readthedocs.io/en/latest/?badge=latest)

# vws-python

Python wrapper for Vuforia Web Services (VWS) API.

See the full documentation at <http://vws-python.readthedocs.io/>.

# Installation

This package has not yet been uploaded to PyPI.

This requires Python 3.6+.
Get in touch with `adamdangoor@gmail.com` if you would like to see this with another language.

# Tests

To run the tests, first install the dependencies.

Spell checking requires `enchant`.
This can be installed on macOS, for example, with [Homebrew](http://brew.sh):

```sh
brew install enchant
```

and on Ubuntu with `apt`:

```sh
apt-get install -y enchant
```

Then install the Python dependencies:

```sh
pip install -e .[dev]
```

Create an environment variable file for secrets:

```sh
cp vuforia_secrets.env.example vuforia_secrets.env
```

Some tests require Vuforia credentials.
To run these tests, add the Vuforia credentials to the file `vuforia_secrets.env`.
See "Connecting to Vuforia".

Then run `pytest`:

```sh
pytest
```

## Connecting to Vuforia

To connect to Vuforia,
Vuforia target databases must be created via the Vuforia Web UI.
Then, secret keys must be set as environment variables.

The test infrastructure allows those keys to be set in the file `vuforia_secrets.env`.
See `vuforia_secrets.env.example` for the environment variables to set.

Do not use a target database that you are using for other purposes.
This is because the test suite adds deletes targets.

To create a target database, first create a license key in the [License Manager](https://developer.vuforia.com/targetmanager/licenseManager/licenseListing).
Then, add a database from the [Target Manager](https://developer.vuforia.com/targetmanager).

To find the environment variables to set in the `vuforia_secrets.env` file,
visit the Target Database in the Target Manager and view the "Database Access Keys".

Two databases are necessary in order to run all the tests.
One of those must be an inactive project.
To create an inactive project, delete the license key associated with a database.

Targets sometimes get stuck at the "Processing" stage meaning that they cannot be deleted.
When this happens, create a new target database to use for testing.

## Skipping tests

Set either `SKIP_MOCK` or `SKIP_REAL` to `1` to skip tests against the mock, or tests against the real implementation, for tests which run against both.

## Running on Travis CI

Tests are run on Travis CI.
The configuration for this is in `.travis.yml`.

Travis CI is set up with environment variables for connecting to Vuforia.
These variables include those from `vuforia_secrets.env`.
They also include another set of variables especially for running the tests on the `master` branch.
The tests are run daily against the `master` branch.
This means that when the daily request quota is used, the `master` branch may show as failing on the `README`.
Using the request quota on the `master` branch also leaves fewer requests for regular development.
Therefore, `master` is given its own Vuforia database with separate limits.

These include the variables from `vuforia_secrets.env` prefixed with `MASTER_`.

All targets are deleted from the database beween each test.
Therefore there may be conflicts if the test suite is run concurrently as Travis CI is configured to connect to one Vuforia database.
As such, Travis CI is configured not to run multiple instances of the test suite concurrently.

# Documentation

To build the documentation, first install the dependencies:

    pip install --upgrade --editable .[dev]

Then use `make`:

    make -C docs clean html

To open the built documentation:

    open docs/build/html/index.html

The documentation is hosted by ReadTheDocs on <http://vws-python.readthedocs.io/>.

# Mocking Vuforia

Requests made to Vuforia can be mocked.
Using the mock redirects requests to Vuforia made with `requests` to an in-memory implementation.
This works for the provided wrapper because the implementation of that uses `requests`.

There are two ways to use the mock, as a decorator and as a context manager.

```python
import requests
from mock_vws import MockVWS

@MockVWS()
def my_function():
    # This will use the Vuforia mock.
    requests.get('https://vws.vuforia.com/summary')

with MockVWS():
    # This will also use the Vuforia mock.
    requests.get('https://vws.vuforia.com/summary')
```

However, an exception will be raised if any requests to unmocked addresses are made.

## Allowing HTTP requests to unmocked addresses

This can be done by setting the parameter `real_http` to `True` in either the decorator or context manager's instantiation.

For example:

```python
import requests
from mock_vws import MockVWS

@MockVWS(real_http=True)
def my_function():
    # This will use the Vuforia mock.
    requests.get('https://vws.vuforia.com/summary')
    # No exception is raised when a request is made to an unmocked address.
    requests.get('http://example.com')

with MockVWS(real_http=True):
    # This will also use the Vuforia mock.
    requests.get('https://vws.vuforia.com/summary')
    # Again, no exception is raised.
    requests.get('http://example.com')
```

## Authentication

Connecting to the Vuforia Web Services requires an access key and a secret key.
The mock also requires these keys as it provides realistic authentication support.

By default, the mock uses random strings as the access and secret keys.

It is possible to access these keys when using the context manager as follows:

```python
from mock_vws import MockVWS

with MockVWS() as mock:
    access_key = mock.access_key
    secret_key = mock.secret_key
```

To set custom keys, set the `access_key` and `secret_key` parameters in either the decorator or context manager's instantiation.

## Setting the database name

This can be done with the `database_name` parameter.
By default this is a random string.

## Mocking error states

Sometimes Vuforia is in an error state, where requests don't work.
You may want your application to handle these states gracefully, and so it is possible to make the mock emulate these states.

To change the state, use the `state` parameter when calling the mock.

```python
import requests
from mock_vws import MockVWS, States

@MockVWS(state=States.PROJECT_INACTIVE)
def my_function():
    ...
```

These states available in `States` are:

* `WORKING`.
  This is the default state of the mock.
* `PROJECT_INACTIVE`.
  This happens when the license key has been deleted.

The mock is tested against the real Vuforia Web Services.
This ensures that the implemented features of the mock behave, at least to some extent, like the real Vuforia Web Services.
However, the mocks of these error states are based on observations as they cannot be reliably reproduced.

## Differences between the mock and the real Vuforia Web Services

The mock attempts to be realistic, but it was built without access to the source code of the original API.
Please report any issues [here](https://github.com/adamtheturtle/vws-python/issues).
There is no attempt to make the image matching realistic.

The mock responds much more quickly than the real Vuforia Web Services.

Targets in the mock are set to 'processing' for half a second.
In the real Vuforia Web Services, this takes varying lengths of time.

Targets are assigned a rating between 0 and 5 of how good they are for tracking purposes.
In the mock this is a random number between 0 and 5.

Image targets which are not suited to detection are given 'failed' statuses.
The criteria for these images is not defined by the Vuforia documentation.
The mock is more forgiving than the real Vuforia Web Services.
Therefore, an image given a 'success' status by the mock may not be given a 'success' status by the real Vuforia Web Services.

The mock does not check whether the server access and secret keys are valid.
It only checks whether the keys used to set up the mock instance match those used to create requests.

The database summary in the real Vuforia Web Services takes some time to account for images.
The mock is accurate immediately.
