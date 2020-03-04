import datetime
import functools
from urllib.parse import urlparse

import jwt

from lms.validation.authentication import BearerTokenSchema


class JSConfig:  # pylint:disable=too-few-public-methods
    """The config for the app's JavaScript code."""

    def __init__(self, context, request):
        self._context = context
        self._request = request

        # A dict of URLs for the frontend to use.
        self._urls = {}

    @property
    @functools.lru_cache()
    def config(self):
        """
        Return the configuration for the app's JavaScript code.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing

        :rtype: dict
        """
        # This is a lazy-computed property so that if it's going to raise an
        # exception that doesn't happen until someone actually reads it.
        # If it instead crashed in JSConfig.__init__() that would happen
        # earlier in the request processing pipeline and could change the error
        # response.
        #
        # We cache this property (@functools.lru_cache()) so that it's
        # mutable. You can do self.config["foo"] = "bar" and the mutation will
        # be preserved.

        return {
            # The auth token that the JavaScript code will use to authenticate
            # itself to our own backend's APIs.
            "authToken": self._auth_token(),
            # The URL that the JavaScript code will open if it needs the user to
            # authorize us to request a new Canvas access token.
            "authUrl": self._request.route_url("canvas_api.authorize"),
            # Some debug information, currently used in the Gherkin tests.
            "debug": self._debug(),
            # The config object for the Hypothesis client.
            # Our JSON-RPC server passes this to the Hypothesis client over
            # postMessage.
            "hypothesisClient": self._hypothesis_client,
            # What "mode" to put the JavaScript code in.
            # For example in "basic-lti-launch" mode the JavaScript code
            # launches its BasicLtiLaunchApp, whereas in
            # "content-item-selection" mode it launches its FilePickerApp.
            "mode": "basic-lti-launch",
            # The config object for our JSON-RPC server.
            "rpcServer": {
                "allowedOrigins": self._request.registry.settings[
                    "rpc_allowed_origins"
                ],
            },
            # A dict of URLs for the frontend to use.
            # For example: API endpoints for the frontend to call would go in
            # here.
            "urls": self._urls,
        }

    def enable_content_item_selection_mode(self):
        """
        Put the JavaScript code into "content item selection" mode.

        This mode shows teachers an assignment configuration UI where they can
        choose the document to be annotated for the assignment.
        """
        self.config["mode"] = "content-item-selection"

    def _auth_token(self):
        """Return the authToken setting."""
        if not self._request.lti_user:
            return None

        return BearerTokenSchema(self._request).authorization_param(
            self._request.lti_user
        )

    def _debug(self):
        """
        Return some debug information.

        Currently used in the Gherkin tests.
        """
        debug_info = {}

        if self._request.lti_user:
            debug_info["tags"] = [
                "role:instructor"
                if self._request.lti_user.is_instructor
                else "role:learner"
            ]

        return debug_info

    def _grant_token(self, api_url):
        """Return an OAuth 2 grant token the client can use to log in to h."""
        now = datetime.datetime.utcnow()

        claims = {
            "aud": urlparse(api_url).hostname,
            "iss": self._request.registry.settings["h_jwt_client_id"],
            "sub": self._context.h_user.userid,
            "nbf": now,
            "exp": now + datetime.timedelta(minutes=5),
        }

        return jwt.encode(
            claims,
            self._request.registry.settings["h_jwt_client_secret"],
            algorithm="HS256",
        ).decode("utf-8")

    @property
    @functools.lru_cache()
    def _hypothesis_client(self):
        """
        Return the config object for the Hypothesis client.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing
        """
        # This is a lazy-computed property so that if it's going to raise an
        # exception that doesn't happen until someone actually reads it.
        # If it instead crashed in JSConfig.__init__() that would happen
        # earlier in the request processing pipeline and could change the error
        # response.
        #
        # We cache this property (@functools.lru_cache()) so that it's
        # mutable. You can do self._hypothesis_client["foo"] = "bar" and the
        # mutation will be preserved.

        if not self._context.provisioning_enabled:
            return {}

        api_url = self._request.registry.settings["h_api_url_public"]

        return {
            # For documentation of these Hypothesis client settings see:
            # https://h.readthedocs.io/projects/client/en/latest/publishers/config/#configuring-the-client-using-json
            "services": [
                {
                    "apiUrl": api_url,
                    "authority": self._request.registry.settings["h_authority"],
                    "enableShareLinks": False,
                    "grantToken": self._grant_token(api_url),
                    "groups": [self._context.h_groupid],
                }
            ]
        }
