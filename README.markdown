[![Build Status](https://travis-ci.org/hypothesis/lms.svg?branch=master)](https://travis-ci.org/hypothesis/lms)
[![codecov](https://codecov.io/gh/hypothesis/lms/branch/master/graph/badge.svg)](https://codecov.io/gh/hypothesis/lms)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# Hypothesis Canvas App

## Installation and configuration

**Q**: Whoa! This `README` is so long! Which steps do I actually need to take?

**A**:

  * You need to [install and run this application locally](#setup-dev)
  * If you want the Google Drive file picker to be available for configuring assignments/modules, [Configure Google APIs](#google-apis)
  * Install the Hypothesis LMS application for one or more Canvas (LMS) courses:
      * Optionally enable the [Canvas file picker](#canvas-picker) so instructors may select assignment files from Canvas uploads
      * [Install the Hypothesis LMS application for a Canvas/LMS course](#install-app-for-course)
  * You may wish to [configure access to reports](#instance-reports) if you'd like to see details on LTI launch history

### Prerequisites

The Hypothesis LMS app is written for python 3 and uses Node.js and `yarn` for managing front-end assets. You'll need:

* git
* python 3
* [tox](https://tox.readthedocs.io/en/latest/) 3.8 or newer
* [GNU Make](https://www.gnu.org/software/make/)
* Docker
* openssl
* Node.js
* yarn
* local installations of [h](https://github.com/hypothesis/h),
  [client](https://github.com/hypothesis/client) and
  [via](https://github.com/hypothesis/via) (*TODO*: Why?)

<a id="setup-dev"></a>
### Installing this app locally

1. **Clone this repository**

    The following steps assume that you are working within the `lms` project directory.

1. Create a client_credentials auth client in h.

   The LMS app requires the OAuth 2.0 `client_id` and `client_secret` from a
   `client_credentials`-type auth client in h in order to use certain h APIs,
   such as the API for creating users.

   To create the necessary auth client in h:

   1. Log in to your local installation of h as an admin user.

      If you don't have an admin user account for your local h see
      [Accessing the admin interface](http://h.readthedocs.io/en/latest/developing/administration/)
      in the h docs.

   1. Go to <http://localhost:5000/admin/oauthclients/new> and create an auth
      client with these settings:

      <dl>
        <dt>Name</dt>
        <dd>LMS</dd>
        <dt>Authority</dt>
        <dd>lms.hypothes.is</dd>
        <dt>Grant type</dt>
        <dd>client_credentials</dd>
        <dt>Redirect URL</dt>
        <dd>(Leave empty)</dd>
      </dl>

      Click <samp>Register client</samp> and keep the tab open because you'll
      need the generated <samp>Client ID</samp> and <samp>Client secret</samp>
      for setting your environment variables later.

1. Also create a jwt_bearer auth client in h.

   The LMS app also requires the `client_id` and `client_secret` from a
   `jwt_bearer`-type auth client in h in order to generate authorization grant
   tokens for logging in to h user accounts.

   Go to <http://localhost:5000/admin/oauthclients/new> and create an auth
   client with these settings:

      <dl>
        <dt>Name</dt>
        <dd>LMS JWT</dd>
        <dt>Authority</dt>
        <dd>lms.hypothes.is</dd>
        <dt>Grant type</dt>
        <dd>jwt_bearer</dd>
        <dt>Redirect URL</dt>
        <dd>(Leave empty)</dd>
      </dl>

      Click <samp>Register client</samp> and keep the tab open because you'll
      need the generated <samp>Client ID</samp> and <samp>Client secret</samp>
      for setting your environment variables later.

1. **Configure environment variables**

    Setting up [Google API integration](#google-apis) and [application instance reports](#instance-reports) access is optional at this point; you can leave the default values for related environment variables for now, if you like.

    ```bash
    export VIA_URL="https://via.hypothes.is/"
    export JWT_SECRET="some secret string here"

    # The secret should be different for each pyramid instance
    # It should be a 64 character (128 bit) string
    # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/session.html
    export LMS_SECRET="Unique string used for encryption"

    # From Google API integration
    export GOOGLE_CLIENT_ID="Google Oauth Client ID"
    export GOOGLE_DEVELOPER_KEY="Google Api Key"
    export GOOGLE_APP_ID="Google Project Id"

    # For application instance reports access
    # Use lms/util/get_password_hash.py to provide vaues for HASHED_PW and SALT
    export HASHED_PW="my_hashed_password"
    export SALT="my_salt"
    export USERNAME="my_desired_report_username"

    # For using the h API.
    # The values for H_CLIENT_ID, H_CLIENT_SECRET and H_AUTHORITY should come
    # from the auth client that you created in h earlier.
    export H_CLIENT_ID="232c***5121"
    export H_CLIENT_SECRET="eVJ4***rXkk"
    export H_AUTHORITY="lms.hypothes.is"
    export H_API_URL_PUBLIC="http://localhost:5000/api/"
    export H_API_URL_PRIVATE="http://localhost:5000/api/"

    # For logging in to the Hypothesis client.
    # The values for H_JWT_CLIENT_ID and H_JWT_CLIENT_SECRET should come from
    # the jwt_bearer auth client that you created in h earlier.
    export H_JWT_CLIENT_ID="3ac7***71e4"
    export H_JWT_CLIENT_SECRET="OJGx***c8x4"

    # A space-separated list of window origins from which JSON-RPC requests
    # will be accepted over postMessage. In a development environment the
    # Hypothesis client would normally be served from localhost:5000.
    export RPC_ALLOWED_ORIGINS="http://localhost:5000"
    ```

1. **Try out the postgres docker container**

    The app's postgres database runs within a docker container. To start the container:

    ```bash
    docker run --rm -d -p 5433:5432 --name lms-postgres postgres
    ```

    You can subsequently stop the container with:

    ```bash
    docker stop lms-postgres
    ```

<a id="run-webserver"></a>
### Running the app locally

1. Start the psql (database) container if it's not already running:

    ```bash
    $ docker run --rm -d -p 5433:5432 --name lms-postgres postgres
    ```

1. Start the development web server and app:

    ```bash
    $ make dev
    ```

1. Visit [http://localhost:8001/welcome](http://localhost:8001/welcome) in a browser


<a id="google-apis"></a>
### Integrating Google Drive, Picker APIs

The app supports the ability to select documents (for annotation) via Google Drive. These steps allow you to enable that feature. The outcome of this process will be a configured Google project and valid values for the `GOOGLE_APP_ID`, `GOOGLE_DEVELOPER_KEY` and `GOOGLE_CLIENT_ID` environment variables.

1. Sign in to the [Google Developer Console](https://console.developers.google.com/apis/)
1. Create a new project. Set the `GOOGLE_APP_ID` environment variable to the ID for this project.
1. Navigate to the "Credentials" section
1. Generate an API key

    Use the "Create Credentials" option to generate an API key — retain this for the `GOOGLE_DEVELOPER_KEY` environment variable

1. Generate an OAuth client ID.

    Again, use the "Create Credentials" option to generate an OAuth client ID.

    This process involves a few steps (via web forms). The resulting ID string can be used as the value for the `GOOGLE_CLIENT_ID` environment variable.

    As of June, 2018, you'll need to create a "consent screen" before you can generate any OAuth client IDs — enter sensible values in the form fields here.

    For the OAuth client ID form itself:

    * Set application type to `Web Application`
    * The 'Authorized Javascript Origins' list should be edited to include the url of the app. (Hint: this is probably `http://localhost:8001` unless you changed the default settings for this)
    * The Authorized redirect URIs tab can be left blank

1. Enable the needed APIs.

    Head to the "Library" section of the Google developer console and enable:

    * Google Drive API
    * Google Picker API

## Installing the LMS app in Canvas (LMSes)

<a id="canvas-picker"></a>
### Enabling the Canvas File Picker

In order to use the Canvas file picker, you need to generate a developer key and ID within the target Canvas instance.

1. Log in to Canvas as an admin user
1. Navigate to `Admin` then click the name of the root account
1. Navigate to `Developer Keys`, then click `+ Developer Key`.
1. Fill out the form:
    1. For name and email you can enter whatever you please; leave the legacy redirect URI field blank
    1. For the `Redirect URIs` field enter:
        ```
        http://localhost:8001/canvas_oauth_callback
        http://localhost:8001/module_item_launch_oauth_callback
        ```

        *Note*: For QA, replace `localhost:8001` with `qa-lms.hypothes.is`; for production, replace it with `lms.hypothes.is`

     7. Click `Save Key`
 8. Take note of the resulting credentials:

    * The `ID` is the `Developer Key` needed in the following steps
    * The `key` is the `Developer Secret` needed in the following steps

<a id="install-app-for-course"></a>
### Installing the App for a Canvas (LMS) Course

#### Generating a consumer key and secret

The [http://localhost:8001/welcome](http://localhost:8001/welcome) tool is used to generate a consumer key and a secret that will be used when installing the Hypothesis LMS app for a Canvas (LMS) course.

1. With your [dev web server running](#run-webserver), visit [http://localhost:8001/welcome](http://localhost:8001/welcome) in a browser.
1. Enter the domain for the Canvas instance where the Hypothesis LMS app will be installed (e.g. `foo.instructure.com`)
1. Enter your email (any email is fine here)
1. To enable Canvas picker integration, enter the Developer Key and Developer Secret generated during the [the Canvas Picker configuration step](#canvas-picker) into the corresponding fields here

#### Installing the Hypothesis LMS app for a Canvas (LMS) Course

1. Log into the your Canvas instance as an admin user
1. Navigate to the course you'd like to add the Hypothesis app to
1. Add a new app for the course

    Navigate to `Settings` and then to the `Apps` tab. Click the `View App Configurations` button, and then the `+ App` (add an app) button.

1. Fill out the Add-App form

    * For `Configuration Type`, select `Paste XML`
    * Give your App a name
    * Enter the consumer key and secret you generated (above) in the provided fields
    * Visit [http://localhost:8001/config_xml](http://localhost:8001/config_xml) and paste the contents of the output into the `XML Configuration` field
    * Submitting the form should install the app and it should be available from within the Modules and Assignments areas of the course

### Configuring Assignments and Modules

**TODO**

When creating a new module or assignment, select `External Tool` and `Hypothesis` from the available list. This should allow you to choose a file from [Google Drive](#google-apis) or [Canvas](#canvas-picker) itself (if you have configured either of those features).

#### Bypassing the browser's "unsafe scripts" (mixed content) blocking

If you use our hosted Canvas instance at <https://hypothesis.instructure.com/>
to test your local dev instance of the app you'll get "unsafe scripts" or "mixed content"
warnings from your browser. This is because hypothesis.instructure.com uses https but your
local dev app, which is running in an iframe in hypothesis.instructure.com, only uses http.

You'll see a blank iframe in Canvas where the app should be, along with a warning about
"trying to launch insecure content" like this:

!["Trying to launch insecure content" error](docs/images/trying-to-launch-insecure-content.png "'Trying to launch insecure content' error")

If you open the browser's developer console you should see an error message like:

    Mixed Content: The page at 'https://hypothesis.instructure.com/...' was loaded over HTTPS,
    but requested an insecure form action 'http://localhost:8001/...'. This request has been
    blocked; the content must be served over HTTPS.

Fortunately you can easily bypass this mixed content blocking by your browser.
You should also see an "Insecure content blocked" icon in the top right of the location bar:

!["Insecure content blocked" dialog](docs/images/insecure-content-blocked.png "'Insecure content blocked' dialog")

Click on the <samp>Load unsafe scripts</samp> link and the app should load successfully.

<a id="instance-reports"></a>
### Application Instance Reports

To enable a report of application instances in the DB, you'll need to define the `USERNAME`, `HASHED_PW` and `SALT` environment variables—this will establish credentials so that the reports may be viewed.

#### Configuring a Username and Password

* Run the command-line script `lms/util/get_password_hash.py`. It will generate a value for `HASHED_PW` and `SALT`
* Set `USERNAME` to the desired username for accessing these reports
* When the webserver is running, you can access the reports in a browser at [http://localhost:8001/reports](http://localhost:8001/reports)

## Development

### Running tests

1. Create the test database. You only need to do this once:

   ```bash
   $ psql postgresql://postgres@localhost:5433/postgres -c "CREATE DATABASE lms_test;"
   ```

1. Run the tests:

   ```bash
   $ make test
   ```

### Interacting with shell, database

#### Shell

`make shell` will get you a Python shell with a Pyramid registry, request, etc.
Useful for debugging or trying things out in development:

```bash
$ make shell
```

#### Database

**Tip**: You can connect to the app's database to inspect its contents by
installing [psql](https://www.postgresql.org/docs/current/static/app-psql.html)
and then running:

```bash
$ make psql
```

**Tip**: If you want to delete all your data and reset your dev database,
an easy way to do so is just to delete the whole docker container:

```bash
$ sudo docker rm lms-postgres
```

You can then re-create the container by re-running the `docker run` command
above.

### Running the linter

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
[lms/migrations/versions](lms/migrations/versions)) for details, but the basic
steps to create a new migration script for h are:

1. Create the revision script by running `alembic revision`, for example:

   ```bash
   $ .tox/py36-dev/bin/alembic -c conf/alembic.ini revision -m "Add the foobar table."
   ```

   This will create a new script in [lms/migrations/versions](lms/migrations/versions).

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
   $ .tox/py36-dev/bin/alembic -c conf/alembic.ini stamp <revision_id>
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
   $ .tox/py36-dev/bin/alembic -c conf/alembic.ini upgrade head
   ```

   After running this command inspect your database's schema to check that it's
   as expected, and run the app to check that everything is working.

   **Note**: You should make sure that there's some repesentative data in the
   relevant columns of the database before testing upgrading and downgrading
   it. Some migration script crashes will only happen when there's data
   present.

1. Test your `downgrade()` function:

   ```bash
   $ .tox/py36-dev/bin/alembic -c conf/alembic.ini downgrade -1
   ```

   After running this command inspect your database's schema to check that it's
   as expected. You can then upgrade it again:

   ```bash
   $ .tox/py36-dev/bin/alembic -c conf/alembic.ini upgrade +1
   ```
