[![Build Status](https://travis-ci.org/adamtheturtle/vws-python.svg?branch=master)](https://travis-ci.com/adamtheturtle/vws-python)
[![Coverage Status](https://coveralls.io/repos/github/adamtheturtle/vws-python/badge.svg)](https://coveralls.io/github/adamtheturtle/vws-python)
[![Requirements Status](https://requires.io/github/adamtheturtle/vws-python/requirements.svg?branch=master)](https://requires.io/github/adamtheturtle/vws-python/requirements/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/vws-python/badge/?version=latest)](http://vws-python.readthedocs.io/en/latest/?badge=latest)

# vws-python

Python wrapper for Vuforia Web Services (VWS) API.

See the full documentation at <http://vws-python.readthedocs.io/>.

# Installation

This package has not yet been uploaded to PyPI.

This requires Python 3.5+.
Get in touch with `adamdangoor@gmail.com` if you would like to see this with another language.

# Tests

To run the tests, first install the dependencies:

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
a Vuforia target database must be created via the Vuforia Web UI.
Then, secret keys must be set as environment variables.

The test infrastructure allows those keys to be set in the file `vuforia_secrets.env`.
See `vuforia_secrets.env.example` for the environment variables to set.

To create a target database, first create a license key in the [License Manager](https://developer.vuforia.com/targetmanager/licenseManager/licenseListing).
Then, add a database from the [Target Manager](https://developer.vuforia.com/targetmanager).

To find the environment variables to set in the `vuforia_secrets.env` file,
visit the Target Database in the Target Manager and view the "Database Access Keys".

# Documentation

To build the documentation, first install the dependencies:

    pip install -e .[dev]

Then use `make`:

    make -C docs clean html

To open the built documentation:

    open docs/build/html/index.html

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
This can be changd by setting the parameter `real_http` to `True` in either the decorator or context manager's instantiation.

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

The mock attempts to be realistic, but it was built without access to the source code of the original API.
Please report any issues [here](https://github.com/adamtheturtle/vws-python/issues).
There is no attempt to make the image matching realistic.
>>>>>>> origin/master
