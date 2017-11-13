[![Build Status](https://travis-ci.org/hypothesis/lms.svg?branch=master)](https://travis-ci.org/hypothesis/lms)
[![codecov](https://codecov.io/gh/hypothesis/lms/branch/master/graph/badge.svg)](https://codecov.io/gh/hypothesis/lms)
[![Updates](https://pyup.io/repos/github/hypothesis/lms/shield.svg)](https://pyup.io/repos/github/hypothesis/lms/)
[![Python 3](https://pyup.io/repos/github/hypothesis/lms/python-3-shield.svg)](https://pyup.io/repos/github/hypothesis/lms/)

# Hypothesis Canvas App

## Development

### Setting up a dev environment

You will need:

* Git
* Python
* Virtualenv
* Docker
* openssl
* You'll need [h](https://github.com/hypothesis/h),
  [client](https://github.com/hypothesis/client) and
  [via](https://github.com/hypothesis/via) development environments running
* ...

1. Run a PostgreSQL database.

   The easiest way to run a database with the configuration that the app
   expects is with Docker. The first time you run it you'll need to use this
   command to create and run the `lms-postgres` docker container:

   ```bash
   $ sudo docker run -p 5433:5432 --name lms-postgres postgres
   ```

   Subsequently you can just re-start the already-created container with:

   ```bash
   sudo docker start -a lms-postgres
   ```

   **Tip**: You can connect to this database to inspect its contents by
   installing [psql](https://www.postgresql.org/docs/current/static/app-psql.html)
   and then running:

   ```bash
   $ psql postgresql://postgres@localhost:5433/postgres
   ```

   **Tip**: If you want to delete all your data and reset your dev database,
   an easy way to do so is just to delete the whole docker container:

   ```bash
   $ sudo docker rm lms-postgres
   ```

   You can then re-create the container by re-running the `docker run` command
   above.

2. Clone the  app's GitHub repository:

   ```bash
   $ git clone git@github.com:atomicjolt/hypothesis_lti.git
   $ cd lti
   ```

3. Set the environment variables that the app needs to values suitable for
   local development:

   ```bash
   export LMS_SERVER="http://localhost:8001"
   export LMS_CREDENTIALS_URL="http://localhost:8001/lti_credentials"
   export CLIENT_ORIGIN="http://localhost:5000"
   export VIA_URL="http://localhost:9080"
   export JWT_SECRET="some secret"
   ```

4.   First create and activate a Python virtual
   environment for the Canvas app
   ```
     virtualenv .
     source  bin/activate
   ```

5. Run the development server. You will need to follow the instructions for setting up ssl if you have not done that already:

   ```bash
   $ make dev
   ```

6. TODO Add app to a canvas course

### Setting up SSL

The server will need to be able to accept requests via https. The easiest way to do this is to create a self signed cert. Follow these instructions (for mac):
1. Create a directory called ssl in the project directory (this folder is git ignored)
```bash
$ mkdir ssl
$ cd ssl
```
2. If you don't have openssl you can install it with brew. Once installed run:
```bash
$ openssl genrsa -des3 -passout pass:x -out server.pass.key 2048
$ openssl rsa -passin pass:x -in server.pass.key -out server.key
$ rm server.pass.key
$ openssl req -new -key server.key -out server.csr
```
You will be prompted to enter some information. It doesn't matter what you enter but you will probably want to leave the challenge password blank.

3. Run this command:
```bash
$ openssl x509 -req -sha256 -days 365 -in server.csr -signkey server.key -out server.crt
```

You should now have a file called `server.key` and `server.crt` in that folder.

4. Enable unsecure localhost in your browser. In chrome this can by entering the folling into the url bar.
```
  chrome://flags/#allow-insecure-localhost
```
Click enable.

5. Verify by running `make dev` and by going to `https://localhost:8001`

### Running the tests

1. Create the test database. You only need to do this once:

   ```bash
   $ psql postgresql://postgres@localhost:5433/postgres -c "CREATE DATABASE lti_test;"
   ```

2. Run the tests:

   ```bash
   $ make test
   ```

### Getting a shell

`make shell` will get you a Python shell with a Pyramid registry, request, etc.
Useful for debugging or trying things out in development:

```bash
$ make shell
```

**Tip**: If you install `pyramid_ipython` then `make shell` will give you an
IPython shell instead of a plain Python one:

```
$ pip install pyramid_ipython
```

There are also `pyramid_` packages for `bpython`, `ptpython`, etc.

### Running the linters

```bash
$ make lint
```

### Managing Python dependencies

We use `pip-tools` to manage Python dependencies: <https://github.com/jazzband/pip-tools>.

#### To add a new Python dependency

Python dependencies are tracked in the [requirements.in][] file
or [requirements-dev.in][] if the requirement is only needed in development
environments and not in production.

In addition `requirements.in` is compiled to produce a [requirements.txt][]
file that pins the version numbers of all dependencies for deterministic
production builds.

**If you've added a new Python dependency**:

1. Add it to `requirements.in` or `requirements-dev.in`.

   You don't usually need to specify the version number of a dependency in
   `requirements.in` or `requirements-dev.in`, nor do you need to list
   dependencies of dependencies, you can just list the top-level dependencies.

2. **If you've added a dependency to `requirements.in`** then update
   `requirements.txt` by running `pip-compile`:

   ```bash
   $ pip-compile --output-file requirements.txt requirements.in
   ```

3. Commit all changed requirements files - `requirements.in`,
   `requirements-dev.in` and `requirements.txt` - to git.

#### To upgrade a Python dependency

For example to upgrade the `requests` dependency to the latest version run:

```bash
$ pip-compile --upgrade-package requests
```

then commit the modified `requirements.txt` file to git.

You can also just run `pip-compile --upgrade` to upgrade all dependencies at
once.

[requirements.in]: requirements.in
[requirements-dev.in]: requirements-dev.in
[requirements.txt]: requirements.txt
[installing_the_app]: https://docs.google.com/document/d/13FFtk2qRogtU3qxR_oa3kq2ak-S_p7HHVnNM12eZGy8/edit# "Installing the App Google Doc"
[using_the_app]: https://docs.google.com/document/d/1EvxGoX81H8AWDcskDph8dmu4Ov4gMSkGGXr5_5ggx3I/edit# "Using the App Google Doc"

### Making changes to model code

If you've made any changes to the database schema (for example: added or
removed a SQLAlchemy ORM class, or added, removed or modified a
`sqlalchemy.Column` on an ORM class) then you need to create a database
migration script that can be used to upgrade the production database from the
previous to your new schema.

**See Also**: [Some tips on writing good migration scripts in the h docs](http://h.readthedocs.io/en/latest/developing/making-changes-to-model-code/#batch-deletes-and-updates-in-migration-scripts).

We use [Alembic](http://alembic.zzzcomputing.com/en/latest/) to create and run
migration scripts. See the Alembic docs (and look at existing scripts in
[lti/migrations/versions](lti/migrations/versions)) for details, but the basic
steps to create a new migration script for h are:

1. Create the revision script by running `alembic revision`, for example:

   ```bash
   $ alembic revision -m "Add the foobar table."
   ```

   This will create a new script in [lti/migrations/versions](lti/migrations/versions).

1. Edit the generated script, fill in the `upgrade()` and `downgrade()` methods.

   See <http://alembic.zzzcomputing.com/en/latest/ops.html#ops> for details.

   **Note**: Not every migration should have a ``downgrade()`` method. For
   example if the upgrade removes a max length constraint on a text field, so
   that values longer than the previous max length can now be entered, then a
   downgrade that adds the constraint back may not work with data created using
   the updated schema.

1. Stamp your database.

   Before running any upgrades or downgrades you need to stamp the database
   with its current revision, so Alembic knows which migration scripts to run:

   ```bash
   $ alembic -c conf/alembic.ini stamp <revision_id>
   ```

   `<revision_id>` should be the revision corresponding to the version of the
   code that was present when the current database was created. The will
   usually be the `down_revision` from the migration script that you've just
   generated.

1. Test your `upgrade()` function by upgrading your database to the most recent
   revision. This will run all migration scripts newer than the revision that
   your db is currently stamped with, which usually means just your new
   revision script:

   ```bash
   $ alembic -c conf/alembic.ini upgrade head
   ```

   After running this command inspect your database's schema to check that it's
   as expected, and run the app to check that everything is working.

   **Note**: You should make sure that there's some repesentative data in the
   relevant columns of the database before testing upgrading and downgrading
   it. Some migration script crashes will only happen when there's data
   present.

1. Test your `downgrade()` function:

   ```bash
   $ alembic -c conf/alembic.ini downgrade -1
   ```

   After running this command inspect your database's schema to check that it's
   as expected. You can then upgrade it again:

   ```bash
   $ alembic -c conf/alembic.ini upgrade +1
   ```
