[![Build Status](https://travis-ci.org/hypothesis/lms.svg?branch=master)](https://travis-ci.org/hypothesis/lms)
[![codecov](https://codecov.io/gh/hypothesis/lms/branch/master/graph/badge.svg)](https://codecov.io/gh/hypothesis/lms)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# Hypothesis LMS App

## Overview and code design

There are three presentations for developers that describe what the Hypothesis LMS app is and how it works. The **speaker notes** in these presentations also contain additional notes and links:

1. [LMS App Demo & Architecture](https://docs.google.com/presentation/d/1eRMjS5B8Yja6Aupp8oKi-UztIJ9_8KRViSc6OMDLfMY/)
2. [LMS App Code Design Patterns](https://docs.google.com/presentation/d/1AWcDoHaV9aAvInefR54SJepZiNM08Zou9jxNssccw3c/)
3. [Speed Grader Workshop](https://docs.google.com/presentation/d/1TJF9SXRMbtHCPnkD9sy-TXe_u55--zYt6veVW0M6leA/) (about the design of the first version of our Canvas Speed Grader support)

## Installing the Hypothesis LMS app in a development environment

### You will need

* The LMS app integrates h, the Hypothesis client and Via, so you will need to
  set up development environments for each of those before you can develop the
  LMS app:

  * https://h.readthedocs.io/en/latest/developing/install/
  * https://h.readthedocs.io/projects/client/en/latest/developers/developing/
  * https://github.com/hypothesis/via

* [Git](https://git-scm.com/)

* [Node](https://nodejs.org/) and npm.
  On Linux you should follow
  [nodejs.org's instructions for installing node](https://nodejs.org/en/download/package-manager/)
  because the version of node in the standard Ubuntu package repositories is
  too old.
  On macOS you should use [Homebrew](https://brew.sh/) to install node.

* [Docker](https://docs.docker.com/install/).
  Follow the [instructions on the Docker website](https://docs.docker.com/install/)
  to install "Docker Engine - Community".

* [pyenv](https://github.com/pyenv/pyenv)
  Follow the instructions in the pyenv README to install it.
  The Homebrew method works best on macOS.

* [Yarn](https://yarnpkg.com/)

* `pg_config`. On Ubuntu: `sudo apt install libpq-dev`. On macOS: `brew install postgresql`.

### Clone the Git repo

    git clone https://github.com/hypothesis/lms.git

This will download the code into an `lms` directory in your current working
directory. You need to be in the `lms` directory from the remainder of the
installation process:

    cd lms

### Run the services with Docker Compose

Start the services that the LMS app requires using Docker Compose:

    make services

### Create a client_credentials auth client in h

The LMS app requires the OAuth 2.0 `client_id` and `client_secret` from a
`client_credentials`-type auth client in h in order to use certain h APIs, such
as the API for creating users.

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

   Click <samp>Register client</samp> and **keep the tab open** because you'll
   need the generated <samp>Client ID</samp> and <samp>Client secret</samp> for
   setting your environment variables later.

### Create a jwt_bearer auth client in h

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

Click <samp>Register client</samp> and **keep the tab open** because you'll
need the generated <samp>Client ID</samp> and <samp>Client secret</samp> for
setting your environment variables later.

### Set environment variables

The LMS app requires several environment variables to be set. Set the following
environment variables in your shell. Notice that:

* You need to replace the `H_CLIENT_ID`, `H_CLIENT_SECRET`, `H_AUTHORITY`,
  `H_JWT_CLIENT_ID` and `H_JWT_CLIENT_SECRET` values below with the ones you
  generated in your local h instance, when you
  were following the instructions above to create auth clients in h.
* We're going to use dummy values for certain required environment variables
  just to get the app to start up. Those features will not be working
  correctly. Below we'll link to docs for setting up those features correctly.

      # The values for H_CLIENT_ID, H_CLIENT_SECRET, H_AUTHORITY, H_JWT_CLIENT_ID
      # and H_JWT_CLIENT_SECRET should come from the auth clients that you
      # created in h earlier.
      export H_CLIENT_ID="232c***5121"
      export H_CLIENT_SECRET="eVJ4***rXkk"
      export H_AUTHORITY="lms.hypothes.is"
      export H_JWT_CLIENT_ID="3ac7***71e4"
      export H_JWT_CLIENT_SECRET="OJGx***c8x4"

      # Dummy settings for Google Drive integration.
      # You'll have to fix these later if you want the Google Drive integration
      # to work.
      export GOOGLE_CLIENT_ID="Google Oauth Client ID"
      export GOOGLE_DEVELOPER_KEY="Google Api Key"
      export GOOGLE_APP_ID="Google Project Id"

      # This sets the password for the /reports page to "password".
      export USERNAME=jeremy
      export HASHED_PW=dc689132a20abfe8d91dcd94cacf698d747a883e682359ffdeef4a2d6e00cc9f
      export SALT=eaeae5723c1772a2

      export VIA_URL="http://localhost:9080"
      export JWT_SECRET="some secret string here"
      export LMS_SECRET="unique string used for encryption"
      export H_API_URL_PUBLIC="http://localhost:5000/api/"
      export H_API_URL_PRIVATE="http://localhost:5000/api/"
      export RPC_ALLOWED_ORIGINS="http://localhost:5000"

### Start the development server

    make dev

The first time you run `make dev` it might take a while to start because it'll
need to install the application dependencies and build the client assets.

This will start the server on port 8001 (http://localhost:8001), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

**That's it!** You’ve finished setting up your lms development environment. Run
`make help` to see all the commands that're available for running the tests,
linting, code formatting, Python and SQL shells, etc.

### Run the tests

You should now be able to run the tests successfully by typing:

    make test

### Further steps

* [Getting the Google Drive integration working locally](docs/google-drive.md)
* [Installing your local lms app in Canvas](docs/canvas.md)

### Bypassing the browser's "unsafe scripts" (mixed content) blocking

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
