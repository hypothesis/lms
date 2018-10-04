import datetime
import urllib

import jwt
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import Allow

from lms import util


class Root:
    """The default root factory for the application."""

    __acl__ = [(Allow, "report_viewers", "view")]

    def __init__(self, request):
        """Return the default root resource object."""
        self.request = request

    @property
    def hypothesis_config(self):
        """
        Return the Hypothesis client config object for the current request.

        Return a dict suitable for dumping to JSON and using as a Hypothesis
        client config object. Includes settings specific to the current LTI
        request, such as an authorization grant token for the client to use to
        log in to the Hypothesis account corresponding to the LTI user that the
        request comes from.

        See: https://h.readthedocs.io/projects/client/en/latest/publishers/config/#configuring-the-client-using-json

        """
        if not self._auto_provisioning_feature_enabled:
            return {}

        client_id = self.request.registry.settings["h_jwt_client_id"]
        client_secret = self.request.registry.settings["h_jwt_client_secret"]
        api_url = self.request.registry.settings["h_api_url"]
        authority = self.request.registry.settings["h_authority"]
        audience = urllib.parse.urlparse(api_url).hostname

        def grant_token():
            now = datetime.datetime.utcnow()
            username = util.generate_username(self.request.params)
            claims = {
                "aud": audience,
                "iss": client_id,
                "sub": "acct:{}@{}".format(username, authority),
                "nbf": now,
                "exp": now + datetime.timedelta(minutes=5),
            }
            return jwt.encode(claims, client_secret, algorithm="HS256")

        return {
            "services": [
                {
                    "apiUrl": api_url,
                    "authority": authority,
                    "grantToken": grant_token().decode("utf-8"),
                }
            ]
        }

    @property
    def rpc_server_config(self):
        """Return the config object for the JSON-RPC server."""
        allowed_origins = self.request.registry.settings["rpc_allowed_origins"]
        return {"allowedOrigins": allowed_origins}

    @property
    def _auto_provisioning_feature_enabled(self):
        try:
            oauth_consumer_key = self.request.params["oauth_consumer_key"]
        except KeyError:
            raise HTTPBadRequest(
                f'Required parameter "oauth_consumer_key" missing from LTI params'
            )
        enabled_consumer_keys = self.request.registry.settings["auto_provisioning"]
        return oauth_consumer_key in enabled_consumer_keys
