# Contributing to VWS Python Mock

Contributions to this repository must pass tests and linting.

Travis CI is the canonical source truth.

## Install Contribution Dependencies

Install dependencies in a virtual environment.

```sh
pip install --editable .[dev]
```

Spell checking requires `enchant`.
This can be installed on macOS, for example, with [Homebrew](http://brew.sh):

```sh
brew install enchant
```

and on Ubuntu with `apt`:

```sh
apt-get install -y enchant
```

## Linting

Run lint tools:

```sh
make lint
```

To fix some lint errors, run the following:

```sh
make fix-lint
```

## Running tests

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
This is because the test suite adds and deletes targets.

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

Travis CI is set up with secrets for connecting to Vuforia.
These variables include those from `vuforia_secrets.env.example`.

To avoid hitting request quotas and to avoid conflicts when running multiple tests in prallel, we use multiple target databases.

### How to set Travis CI secrets

Create environment variable files for secrets:

```sh
mkdir -p ci_secrets
cp vuforia_secrets.env.example ci_secrets/vuforia_secrets_0.env
cp vuforia_secrets.env.example ci_secrets/vuforia_secrets_1.env
...
```

Add Vuforia credentials for different target databases to the new files in the `ci_secrets/` directory.
The more credentials files there are, the more tests can run in parallel on Travis CI.
This is up to a maximum of five, as Travis CI allows five concurrent jobs for open source projects.

Install the Travis CLI:

```sh
gem install travis --no-rdoc --no-ri
```

Limit the number of concurrent jobs to the number of credentials files, e.g.:

```sh
travis settings maximum_number_of_builds --set 5
```

Add the encrypted secrets files to the repository and Travis CI:

```sh
tar cvf secrets.tar ci_secrets/
travis encrypt-file secrets.tar --add --force
git add secrets.tar.enc .travis.yml
git commit -m 'Update secret archive'
git push
```

Note that the [Travis CI documentation](https://docs.travis-ci.com/user/encrypting-files/#Caveat) warns that this might not work on Windows.

### Travis CI Settings

All targets are deleted from the database between each test.
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

Some of the [Vuforia Web Services documentation](https://library.vuforia.com/articles/Training/Image-Target-Guide) states that "The size of the input images must 2 MB or less".
However, other [Vuforia Web Services documentation](https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query) is more accurate:
"Maximum image size: 2.1 MPixel. 512 KiB for JPEG, 2MiB for PNG".

The documentation page [How To Perform an Image Recognition Query](https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query) states that the `Content-Type` header must be set to `multipart/form-data`.
However, it must be set to `multipart/form-data; boundary=<BOUNDARY>` where `<BOUNDARY>` is the boundary used when encoding the form data.

The documentation page [How To Perform an Image Recognition Query](https://library.vuforia.com/articles/Solution/How-To-Perform-an-Image-Recognition-Query) states that `Content-Type` with be the only response header.
This is not the case.

## Performing a release

There is currently no release process.
See [this issue](https://github.com/adamtheturtle/vws-python/issues/55) for details.
