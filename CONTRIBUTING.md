# Contributing to VWS Python Mock

Contributions to this repository must pass tests and linting.

Travis CI is the canonical source truth.

## Running tests

To run the tests locally, first install the dependencies.

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

## Skipping some tests

Set either `SKIP_MOCK` or `SKIP_REAL` to `1` to skip tests against the mock, or tests against the real implementation, for tests which run against both.

## Travis CI

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

## Learnings about VWS

Vuforia Web Services, at the time of writing, does not behave exactly as documented.

The following list includes details of differences between VWS and expected or documented behaviour.

When attempting to delete a target immediately after creating it, a `FORBIDDEN` response is returned.
This is because the target goes into a processing state.

`image` is required for `POST /targets`, but it is documented as not mandatory.

The `tracking_rating` returned by `GET /targets/<target_id>` can be -1.

The database summary from `GET /summary` has multiple undocumented return fields.

The database summary from `GET /summary` has is not immediately accurate.
