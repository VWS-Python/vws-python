[![Build Status](https://travis-ci.org/adamtheturtle/vws-python.svg?branch=master)](https://travis-ci.org/adamtheturtle/vws-python)
[![codecov](https://codecov.io/gh/adamtheturtle/vws-python/branch/master/graph/badge.svg)](https://codecov.io/gh/adamtheturtle/vws-python)
[![Requirements Status](https://requires.io/github/adamtheturtle/vws-python/requirements.svg?branch=master)](https://requires.io/github/adamtheturtle/vws-python/requirements/?branch=master)

# vws-python

Python wrapper for Vuforia Web Services (VWS) API.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for details on how to contribute to this repository.

## Installation

This package has not yet been uploaded to PyPI.

This requires Python 3.6+.
Get in touch with `adamdangoor@gmail.com` if you would like to see this with another language.

## Mocking Vuforia

Requests made to Vuforia can be mocked.
Using the mock redirects requests to Vuforia made with `requests` to an in-memory implementation.

```python
import requests
from mock_vws import MockVWS

with MockVWS():
    # This will use the Vuforia mock.
    requests.get('https://vws.vuforia.com/summary')
```

However, an exception will be raised if any requests to unmocked addresses are made.

### Allowing HTTP requests to unmocked addresses

This can be done by setting the parameter `real_http` to `True` in either the context manager's instantiation.

For example:

```python
import requests
from mock_vws import MockVWS

with MockVWS(real_http=True):
    # This will use the Vuforia mock.
    requests.get('https://vws.vuforia.com/summary')
    # No exception is raised when a request is made to an unmocked address.
    requests.get('http://example.com')
```

### Authentication

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

To set custom keys, set the `access_key` and `secret_key` parameters in either the context manager's instantiation.

### Setting the database name

This can be done with the `database_name` parameter.
By default this is a random string.

### Mocking error states

Sometimes Vuforia is in an error state, where requests don't work.
You may want your application to handle these states gracefully, and so it is possible to make the mock emulate these states.

To change the state, use the `state` parameter when calling the mock.

```python
import requests
from mock_vws import MockVWS, States

def my_function():
    with MockVWS(state=States.PROJECT_INACTIVE) as mock:
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
