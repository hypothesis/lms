import configparser
import json
import sys
from wsgiref.simple_server import make_server

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from pyramid.paster import bootstrap

from lms.services import CanvasAPIAccessTokenError
from lms.validation.authentication import BearerTokenSchema
from lms.values import LTIUser


__all__ = ["devdata"]


def json_format(obj):
    """Return ``obj`` as a pretty-printed JSON string."""
    json_str = json.dumps(obj, indent=4, sort_keys=True)
    return highlight(json_str, JsonLexer(), TerminalFormatter())


class Config:
    """The configuration settings (read from the config file)."""

    def __init__(self, config_uri):
        config = configparser.ConfigParser()
        config.read(config_uri)
        self.host = config["server:main"]["host"]
        self.port = int(config["server:main"]["port"])


class App:
    """An instance of the LMS app that can respond on a host and port."""

    def __init__(self, config, env):
        self._host = config.host
        self._port = config.port

        self._server = make_server(self._host, self._port, env["app"])

        request = env["request"]

        # self._route_url() will be a function for generating URLs.
        self._route_url = request.route_url

        # self._authorization_param() will be a function for generating fresh
        # authorization params.
        self._authorization_param = lambda: BearerTokenSchema(
            request
        ).authorization_param(request.lti_user)

        # self._authorization_url() will be a function for generating fresh
        # authorization URLs (with fresh authorization params in them).
        self._authorization_url = lambda: self._route_url(
            "canvas_api.authorize",
            _query=[("authorization", self._authorization_param())],
            _host=self._host,
            _port=self._port,
        )

    def get_new_access_token(self):
        """Get a new Canvas API access token and save it to the DB.

        Print out a URL that the user can open in their browser (where they must
        log in or already be logged in as the correct Canvas user) in order to get
        a new Canvas API access token and save it to the LMS app's DB.

        This function will attempt to block until a new access token has been saved
        to the DB, and then return. But this isn't guaranteed: there still might
        not be a new access token in the DB after the function returns.
        """
        # Print out the URL that the user must open in their browser in order to
        # authorize the app in Canvas.
        print(self._authorization_url())

        # Wait until the LMS app has responded to two requests before returning.
        #
        # These two requests will likely be:
        #
        # 1. The initial authorization URL request from the use opening the URL
        #    that we just printed out (the app will redirect the user to Canvas's
        #    OAuth 2 authorization page)
        # 2. The redirect request with an authorization code from Canvas after the
        #    user has clicked [Authorize] in Canvas. The app will have used the
        #    authorization code to try to get a new access token and save it to the
        #    DB.
        #
        # So after these two requests have been handled there is likely a new
        # access token in the DB. But this isn't guaranteed: for example we can't
        # guarantee that other request to the app haven't happened instead. Nor can
        # we guarantee that exchanging the authorization code for an access token
        # worked.
        self._server.handle_request()
        self._server.handle_request()


class CanvasAPIClient:
    """A wrapper for ``CanvasAPIClient`` that adds command line authorization.

    A wrapper class for :cls:`lms.services.canvas_api.CanvasAPIClient` that
    does command line Canvas OAuth 2 authorization if the request fails.

    If a call to a ``CanvasAPIClient`` method fails with a
    ``CanvasAPIAccessTokenError`` then it prints out a URL that the user can
    open to re-authorize with Canvas (and save a new access token to our DB).
    After re-authorization it re-tries the ``CanvasAPIClient`` method (in an
    infinite loop).
    """

    def __init__(self, config, env):
        self._app = App(config, env)
        self._canvas_api_client = env["request"].find_service(name="canvas_api_client")

    def call(self, method_name, *args, **kwargs):
        method = getattr(self._canvas_api_client, method_name)

        while True:
            try:
                return method(*args, **kwargs)
                break
            except CanvasAPIAccessTokenError:
                self._app.get_new_access_token()


def canvasapi():
    """A command line script for the Canvas API."""

    # The path to the config file (e.g. conf/development.ini).
    config_uri = sys.argv[1]

    with bootstrap(config_uri) as env:
        config = Config(config_uri)

        request = env["request"]

        # TODO: Set from command line args.
        request.lti_user = LTIUser(
            user_id="***",
            oauth_consumer_key="***",
            roles="Instructor",
        )

        request.tm.begin()

        try:
            response = CanvasAPIClient(config, env).call("list_files", "83")
        finally:
            request.tm.commit()

        json_str = json_format(response)
        print(json_str)
