import datetime
import urllib

import jwt
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import Allow

from lms import models
from lms import util
from lms.util import lti_params_for


class Root:
    """The default root factory for the application."""

    __acl__ = [(Allow, "report_viewers", "view")]

    def __init__(self, request):
        """Return the default root resource object."""
        self._request = request


class LTILaunch:
    """Context resource for LTI launch requests."""

    DISPLAY_NAME_MAX_LENGTH = 30
    """The maximum length of an h display name."""

    def __init__(self, request):
        """Return the context resource for an LTI launch request."""
        self._request = request
        # This will raise HTTPBadRequest if the request looks like an OAuth
        # redirect request but no DB-stashed LTI params can be found for the
        # request.
        self._lti_params = lti_params_for(request)

    @property
    def h_display_name(self):
        """Return the h user display name for the current request."""
        full_name = (self._lti_params.get("lis_person_name_full") or "").strip()
        given_name = (self._lti_params.get("lis_person_name_given") or "").strip()
        family_name = (self._lti_params.get("lis_person_name_family") or "").strip()

        if full_name:
            display_name = full_name
        else:
            display_name = " ".join((given_name, family_name))

        display_name = display_name.strip()

        display_name = display_name or "Anonymous"

        if len(display_name) > self.DISPLAY_NAME_MAX_LENGTH:
            display_name = (
                display_name[: self.DISPLAY_NAME_MAX_LENGTH - 1].rstrip() + "…"
            )

        return display_name

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

        client_id = self._request.registry.settings["h_jwt_client_id"]
        client_secret = self._request.registry.settings["h_jwt_client_secret"]
        api_url = self._request.registry.settings["h_api_url"]
        authority = self._request.registry.settings["h_authority"]
        audience = urllib.parse.urlparse(api_url).hostname

        def grant_token():
            now = datetime.datetime.utcnow()
            username = util.generate_username(self._lti_params)
            claims = {
                "aud": audience,
                "iss": client_id,
                "sub": "acct:{}@{}".format(username, authority),
                "nbf": now,
                "exp": now + datetime.timedelta(minutes=5),
            }
            return jwt.encode(claims, client_secret, algorithm="HS256")

        tool_consumer_instance_guid = self._lti_params.get(
            "tool_consumer_instance_guid"
        )
        context_id = self._lti_params.get("context_id")
        group = models.CourseGroup.get(
            self._request.db, tool_consumer_instance_guid, context_id
        )
        assert group is not None, "The group should always exist by now"

        return {
            "services": [
                {
                    "apiUrl": api_url,
                    "authority": authority,
                    "enableShareLinks": False,
                    "grantToken": grant_token().decode("utf-8"),
                    "groups": [group.pubid],
                }
            ]
        }

    @property
    def rpc_server_config(self):
        """Return the config object for the JSON-RPC server."""
        allowed_origins = self._request.registry.settings["rpc_allowed_origins"]
        return {"allowedOrigins": allowed_origins}

    @property
    def _auto_provisioning_feature_enabled(self):
        try:
            oauth_consumer_key = self._lti_params["oauth_consumer_key"]
        except KeyError:
            raise HTTPBadRequest(
                f'Required parameter "oauth_consumer_key" missing from LTI params'
            )
        enabled_consumer_keys = self._request.registry.settings["auto_provisioning"]
        return oauth_consumer_key in enabled_consumer_keys
