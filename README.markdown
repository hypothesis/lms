# Hypothesis Canvas App

## Development

### Setting up a dev environment

You will need:

* Git
* Python
* Virtualenv
* Docker
* ...

To get the Canvas app running in a dev environment:

1. Set up a dev install of Canvas: <https://github.com/instructure/canvas-lms/wiki/Quick-Start>.

   Tip: you might want to install Canvas inside a virtual machine, to avoid
   installing all that stuff onto your host machine. If you do so you'll have
   to setup virtual machine <-> host machine networking though.

   Tip: Canvas runs on port 3000 by default, which is a port already used by
   the Hypothesis client in development. I moved Canvas to port 3333 in my
   Canvas virtual machine's port forwarding config.

1. You'll also need to install Redis and configure your Canvas dev install to
   use Redis, even though Canvas's Quick Start docs don't say to do so.

   The easiest way to install Redis is by using Docker. Install Docker if you
   don't have it already and then just run:

   ```bash
   $ docker run -p 6379:6379 redis
   ```

   Redis will now be running on <http://localhost:6379/>. You won't see
   anything there in a web browser though because Redis doesn't respond to
   HTTP. Instead you can test it by installing
   [redis-cli](https://redis.io/topics/rediscli) then running `redis-cli ping`:

   ```bash
   $ redis-cli ping
   PONG
   ```

   After installing Redis follow the parts of the
   [Canvas Redis configuration docs](https://github.com/instructure/canvas-lms/wiki/Production-Start#redis)
   where it says to edit your `cache-store.yml` and `redis.yml` files, but
   note that you don't need to do the `chown` and `chmod` commands.

   Here's my `cache-store.yml` file:

   ```
   development:
     cache_store: redis_store
   ```

   And here's my `redis.yml` file:

   ```
   development:
     servers:
     - redis://localhost:6379
   ```

   Tip: if Canvas is running inside a virtual machine and Redis is running in
   a Docker container on the host machine, then the Redis URL above will have
   to be the IP address of the host machine as seen from inside the virtual
   machine, instead of `localhost`. If you setup your virtual machine using
   Vagrant this is `redis://10.0.2.2:6379`.

1. Clone the Hypothesis Canvas app's GitHub repository:

   ```bash
   $ git clone https://github.com/hypothesis/lti.git
   $ cd lti
   ```

1. Set the environment variables that the app needs to values suitable for
   local development:

   ```bash
   export LTI_SERVER_SCHEME="http"
   export LTI_SERVER_HOST="localhost"
   export LTI_SERVER_PORT="8001"
   export LTI_CREDENTIALS_URL="http://localhost:8001/lti_credentials"
   ```

1. Run the development server. First create and activate a Python virtual
   environment for the Canvas app and then run:

   ```bash
   $ make dev
   ```

1. Add the development Hypothesis Canvas app to a course and an assignment in
   your development Canvas instance. Follow the
   [Installing the App][installing_the_app] and [Using the App][using_the_app]
   google docs.

   Tip: In my developer key the **Redirect URI (Legacy)** is set to
   `http://localhost:8001/token_init`.
   
   In the Canvas app's settings I set the **Config URL** to
   `http://10.0.0.2:8001/config` because I have Canvas running inside a VM and
   `10.0.0.2` is the address of my host machine (where the Hypothesis Canvas
   app is running) as seen from within the VM. If you don't have Canvas running
   inside a VM then the Config URL would be `http://localhost:8001/config`.

   Other app URLs, for example the **Launch URL**, are called from the browser
   rather than from the Canvas server, so they should be `localhost:8001` even
   if you're running Canvas inside a VM.

### Running the tests

```bash
$ make test
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
