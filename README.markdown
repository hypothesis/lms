[![Build Status](https://travis-ci.org/hypothesis/lms.svg?branch=master)](https://travis-ci.org/hypothesis/lms)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Coverage: 100%](https://img.shields.io/badge/Coverage-100%25-brightgreen)](https://github.com/hypothesis/lms/blob/master/.coveragerc#L18)

# Hypothesis LMS App

## Installing the Hypothesis LMS app in a development environment

### You will need

* The LMS app integrates h, the Hypothesis client, Via 3, and Via, so you will need to
  set up development environments for each of those before you can develop the
  LMS app:

  * https://h.readthedocs.io/en/latest/developing/install/
  * https://h.readthedocs.io/projects/client/en/latest/developers/developing/
  * https://github.com/hypothesis/via3 (Serves PDF content)
  * https://github.com/hypothesis/via (Serves HTTP content)

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

### Create the development data and settings

Create the database contents and environment variable settings needed to get lms
working nicely with your local development instances of the rest of the
Hypothesis apps, and with our test LMS sites (Canvas, Blackboard, ...):

    make devdata

<details> <summary>Creating data and settings manually instead</summary>

`make devdata` requires you to have a git SSH key set up that has access to the
private https://github.com/hypothesis/devdata repo. Otherwise it'll crash. If
you aren't a Hypothesis team member and don't have access to the devdata repo,
or if you're installing the app in a production environment, you can follow
these instructions to create the necessary data and settings manually:

[Creating the development data and settings manually](docs/manual-data-and-settings.md)
</details>

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

## Overview and code design

There are three presentations for developers that describe what the Hypothesis LMS app is and how it works. The **speaker notes** in these presentations also contain additional notes and links:

1. [LMS App Demo & Architecture](https://docs.google.com/presentation/d/1eRMjS5B8Yja6Aupp8oKi-UztIJ9_8KRViSc6OMDLfMY/)
2. [LMS App Code Design Patterns](https://docs.google.com/presentation/d/1AWcDoHaV9aAvInefR54SJepZiNM08Zou9jxNssccw3c/)
3. [Speed Grader Workshop](https://docs.google.com/presentation/d/1TJF9SXRMbtHCPnkD9sy-TXe_u55--zYt6veVW0M6leA/) (about the design of the first version of our Canvas Speed Grader support)
