"""Traversal resources for LTI launch views."""
import datetime
import hashlib
import urllib

import jwt
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import Allow

from lms.validation.authentication import BearerTokenSchema
from lms.values import HUser

__all__ = ["LTILaunchResource"]


class LTILaunchResource:
    """Context resource for LTI launch requests."""

    DISPLAY_NAME_MAX_LENGTH = 30
    """The maximum length of an h display name."""

    GROUP_NAME_MAX_LENGTH = 25
    """The maximum length of an h group name."""

    USERNAME_MAX_LENGTH = 30
    """The maximum length of an h username."""

    __acl__ = [(Allow, "lti_user", "launch_lti_assignment")]

    def __init__(self, request):
        """Return the context resource for an LTI launch request."""
        self._request = request
        self._authority = self._request.registry.settings["h_authority"]
        self._ai_getter = self._request.find_service(name="ai_getter")
        self._hypothesis_config = None
        self._js_config = None

    @property
    def h_user(self):
        """
        Return the h user for the current request.

        :raise HTTPBadRequest: if any LTI params needed for generating the
          h user are missing
        """
        return HUser(
            authority=self._authority,
            username=self._h_username,
            display_name=self._h_display_name,
        )

    @property
    def _h_display_name(self):
        """Return the h user display name for the current request."""
        full_name = (self._request.params.get("lis_person_name_full") or "").strip()
        given_name = (self._request.params.get("lis_person_name_given") or "").strip()
        family_name = (self._request.params.get("lis_person_name_family") or "").strip()

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
    def h_authority_provided_id(self):
        """
        Return a unique h authority_provided_id for the request's group.

        The authority_provided_id is deterministic and is unique to the LTI
        course. Calling this function again with params representing the same
        LTI course will always return the same authority_provided_id. Calling
        this function with different params will always return a different
        authority_provided_id.

        :raise HTTPBadRequest: if an LTI param needed for generating the
            authority_provided_id is missing
        """
        # Generate the authority_provided_id based on the LTI
        # tool_consumer_instance_guid and context_id parameters.
        # These are "recommended" LTI parameters (according to the spec) that in
        # practice are provided by all of the major LMS's.
        # tool_consumer_instance_guid uniquely identifies an instance of an LMS,
        # and context_id uniquely identifies a course within an LMS. Together they
        # globally uniquely identify a course.
        hash_object = hashlib.sha1()
        hash_object.update(self._get_param("tool_consumer_instance_guid").encode())
        hash_object.update(self._get_param("context_id").encode())
        return hash_object.hexdigest()

    @property
    def h_groupids(self):
        """
        Return the list of h groupids for the current request.

        The returned IDs are suitable for use with the h API's ``groupid``
        parameter.

        The groupids are deterministic and each is unique to the LTI course. Calling this
        function again with params representing the same LTI course will always
        return the same groupids. Calling this function with params
        representing a different LTI course will always return different
        groupids.

        :raise HTTPBadRequest: if an LTI param needed for generating the
            groupids is missing
        """
        return [f"group:{self.h_authority_provided_id}@{self._authority}"]

    @property
    def h_group_name(self):
        """
        Return the h group name for the current request.

        This will usually generate a valid Hypothesis group name from the LTI
        params. For example if the LTI course's title is too long for a Hypothesis
        group name it'll be truncated. But this doesn't currently handle LTI course
        names that are *too short* to be Hypothesis group names (shorter than 3
        chars) - in that case if you try to create a Hypothesis group using the
        generated name you'll get back an unsuccessful response from the Hypothesis
        API.

        :raise HTTPBadRequest: if an LTI param needed for generating the group
          name is missing
        """
        name = self._get_param("context_title").strip()

        if len(name) > self.GROUP_NAME_MAX_LENGTH:
            name = name[: self.GROUP_NAME_MAX_LENGTH - 1].rstrip() + "…"

        return name

    @property
    def h_provider(self):
        """
        Return the h "provider" string for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          provider is missing
        """
        return self._get_param("tool_consumer_instance_guid")

    @property
    def h_provider_unique_id(self):
        """
        Return the h provider_unique_id for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          provider unique ID is missing
        """
        return self._get_param("user_id")

    @property
    def _h_username(self):
        """
        Return the h username for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          username is missing
        """
        hash_object = hashlib.sha1()
        hash_object.update(self.h_provider.encode())
        hash_object.update(self.h_provider_unique_id.encode())
        return hash_object.hexdigest()[: self.USERNAME_MAX_LENGTH]

    @property
    def js_config(self):
        """
        Return the configuration for the app's JavaScript code.

        This is a mutable config dict. It can be accessed, for example by
        views, as ``request.context.js_config``, and they can mutate it or add
        their own view-specific config settings. The modified config object
        will then be passed to the JavaScript code in the response page.

        :rtype: dict
        """
        if self._js_config is None:
            # Initialize self._js_config for the first time.
            self._js_config = {"urls": {}}

            if self._request.lti_user:
                self._js_config["authToken"] = BearerTokenSchema(
                    self._request
                ).authorization_param(self._request.lti_user)

            self.js_config.update(
                **{
                    "tool_consumer_instance_guid": self._get_param(
                        "tool_consumer_instance_guid"
                    ),
                    "lis_person_name_full": self._get_param("lis_person_name_full"),
                    "lis_person_name_given": self._get_param("lis_person_name_given"),
                    "lis_person_name_family": self._get_param("lis_person_name_family"),
                    "context_id": self._get_param("context_id"),
                    "context_title": self._get_param("context_title"),
                }
            )

        return self._js_config

    @property
    def hypothesis_config(self):
        """
        Return the Hypothesis client config object for the current request.

        Return a dict suitable for dumping to JSON and using as a Hypothesis
        client config object. Includes settings specific to the current LTI
        request, such as an authorization grant token for the client to use to
        log in to the Hypothesis account corresponding to the LTI user that the
        request comes from.

        This is a mutable config dict. It can be accessed, for example by
        views, as ``request.context.hypothesis_config``, and they can mutate it or add
        their own view-specific config settings. The modified config object
        will then be passed to the Hypothesis client.

        See: https://h.readthedocs.io/projects/client/en/latest/publishers/config/#configuring-the-client-using-json

        """
        if not self.provisioning_enabled:
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
                "sub": self.h_user.userid,
                "nbf": now,
                "exp": now + datetime.timedelta(minutes=5),
            }
            return jwt.encode(claims, client_secret, algorithm="HS256")

        if self._hypothesis_config is None:
            self._hypothesis_config = {
                "services": [
                    {
                        "apiUrl": api_url,
                        "authority": self._authority,
                        "enableShareLinks": False,
                        "grantToken": grant_token().decode("utf-8"),
                        "groups": self.h_groupids,
                    }
                ]
            }

        return self._hypothesis_config

    @property
    def rpc_server_config(self):
        """Return the config object for the JSON-RPC server."""
        allowed_origins = self._request.registry.settings["rpc_allowed_origins"]
        return {"allowedOrigins": allowed_origins}

    @property
    def provisioning_enabled(self):
        """
        Return True if provisioning is enabled for this request.

        Return True if the provisioning feature is enabled for the current
        request, False otherwise.

        :raise HTTPBadRequest: if there's no oauth_consumer_key in the request
          params
        """
        return self._ai_getter.provisioning_enabled(
            self._get_param("oauth_consumer_key")
        )

    @property
    def lms_url(self):
        """Return the ApplicationInstance.lms_url."""
        oauth_consumer_key = self._request.params.get("oauth_consumer_key")
        return self._ai_getter.lms_url(oauth_consumer_key)

    @property
    def custom_canvas_api_domain(self):
        """
        Return the domain of the Canvas API.

        FIXME: Getting this from the custom_canvas_api_domain param isn't quite
        right. This is the domain of the Canvas API which isn't the same thing
        as the domain of the Canvas website (although in practice it always
        seems to match). And of course custom_canvas_api_domain only works in
        Canvas.
        """
        return self._request.params.get("custom_canvas_api_domain")

    def _get_param(self, param_name):
        """Return the named param from the request or raise a 400."""
        param = self._request.params.get(param_name)
        if not param:
            raise HTTPBadRequest(
                f'Required parameter "{param_name}" missing from LTI params'
            )
        return param
