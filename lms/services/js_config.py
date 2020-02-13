import datetime
import functools
import urllib

import jwt

from lms.validation.authentication import BearerTokenSchema


class JSConfig:
    """A service for generating the config for the app's JavaScript code."""

    def __init__(self, context, request):
        self._context = context
        self._request = request

        # Make the JavaScript config dict available as `request.js_config`
        # for convenient access by templates.
        request.set_property(lambda request: self.config, "js_config", reify=True)

    @property
    @functools.lru_cache()
    def config(self):
        """
        Return the configuration for the app's JavaScript code.

        This is a mutable config dict. It can be accessed, for example by
        views, and they can mutate it or add their own view-specific config
        settings. The modified config object will then be passed to the
        JavaScript code in the response page.

        :rtype: dict
        """
        return {
            "authToken": self._auth_token,
            "hypothesisClient": self._hypothesis_config,
            "rpcServer": self._rpc_server_config,
            "urls": self._urls,
        }

    @property
    def _auth_token(self):
        """Return the authToken setting."""
        if not self._request.lti_user:
            return None

        return BearerTokenSchema(self._request).authorization_param(
            self._request.lti_user
        )

    @property
    def _hypothesis_config(self):
        """
        Return the Hypothesis client config object for the current request.

        See: https://h.readthedocs.io/projects/client/en/latest/publishers/config/#configuring-the-client-using-json

        """
        if not self._context.provisioning_enabled:
            return {}

        client_id = self._request.registry.settings["h_jwt_client_id"]
        client_secret = self._request.registry.settings["h_jwt_client_secret"]
        api_url = self._request.registry.settings["h_api_url_public"]
        audience = urllib.parse.urlparse(api_url).hostname

        def grant_token():
            now = datetime.datetime.utcnow()
            claims = {
                "aud": audience,
                "iss": client_id,
                "sub": self._context.h_user.userid,
                "nbf": now,
                "exp": now + datetime.timedelta(minutes=5),
            }
            return jwt.encode(claims, client_secret, algorithm="HS256")

        return {
            "services": [
                {
                    "apiUrl": api_url,
                    "authority": self._request.registry.settings["h_authority"],
                    "enableShareLinks": False,
                    "grantToken": grant_token().decode("utf-8"),
                    "groups": [self._context.h_groupid],
                }
            ]
        }

    @property
    def _rpc_server_config(self):
        """Return the config for the postMessage-JSON-RPC server."""
        return {
            "allowedOrigins": self._request.registry.settings["rpc_allowed_origins"],
        }

    @property
    def _urls(self):
        """
        Return a dict of URLs for the frontend to use.

        For example: API endpoints for the frontend to call would go in
        here.

        """
        return {}
