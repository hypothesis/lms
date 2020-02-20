import datetime
import functools
from urllib.parse import urlparse

import jwt

from lms.services import HAPIError
from lms.validation.authentication import BearerTokenSchema


class JSConfig:
    """The config for the app's JavaScript code."""

    def __init__(self, context, request):
        self._context = context
        self._request = request

    def enable_basic_lti_launch_mode(self):
        self.config["mode"] = "basic-lti-launch"

    def enable_content_item_selection_mode(self):
        self.config["mode"] = "content-item-selection"

    def add_canvas_submission_params(self, document_url=None, canvas_file_id=None):
        """Add config used by UI to call Canvas's `record_submission` API."""

        # One of document_url or canvas_file_id must be given but not both.
        assert any((document_url is not None, canvas_file_id is not None))
        assert not all((document_url is not None, canvas_file_id is not None))

        if not self._is_canvas:
            return

        lis_result_sourcedid = self._request.params.get("lis_result_sourcedid")
        lis_outcome_service_url = self._request.params.get("lis_outcome_service_url")

        def should_post_submission_to_canvas():
            # When a Canvas assignment is launched by a teacher or other
            # non-gradeable user there's no lis_result_sourcedid in the LTI
            # launch params.
            # Don't post submission to Canvas for these cases.
            if not lis_result_sourcedid:
                return False

            # When a Canvas assignment isn't gradeable there's no
            # lis_outcome_service_url.
            # Don't post submission to Canvas for these cases.
            if not lis_outcome_service_url:
                return False

            return True

        if not should_post_submission_to_canvas():
            return

        self.config["submissionParams"] = {
            "h_username": self._context.h_user.username,
            "lis_result_sourcedid": lis_result_sourcedid,
            "lis_outcome_service_url": lis_outcome_service_url,
        }

        if document_url is not None:
            self.config["submissionParams"]["document_url"] = document_url
        elif canvas_file_id is not None:
            self.config["submissionParams"]["canvas_file_id"] = canvas_file_id

    def set_canvas_focused_user(self):
        """Configure the Hypothesis client to focus on a particular user."""

        if not self._is_canvas:
            return

        # If the launch has been configured to focus on the annotations from
        # a particular user, translate that into Hypothesis client configuration.

        # This parameter is only passed as a part of Canvas SpeedGrader config
        # and is passed as a parameter to a URL which they call us back on.
        focused_user = self._request.params.get("focused_user")
        if not focused_user:
            return

        h_api = self._request.find_service(name="h_api")

        try:
            display_name = h_api.get_user(focused_user).display_name
        except HAPIError:
            # If we couldn't fetch the student's name for any reason, fall back
            # to a placeholder rather than giving up entirely, since the rest
            # of the experience can still work.
            display_name = "(Couldn't fetch student name)"

        # TODO! - Could/should this be replaced with a GradingInfo lookup?
        self._hypothesis_config["focus"] = {
            "user": {"username": focused_user, "displayName": display_name}
        }

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
            # The URL that the JavaScript code will open if it needs the user to
            # authorize us to request a new access token.
            "authUrl": self._request.route_url("canvas_api.authorize"),
            "debug": self._debug,
            "hypothesisClient": self._hypothesis_config,
            # The LMS name to use in user-facing messages.
            # Shown on the "Select PDF from Canvas" button label.
            "lmsName": "Canvas",
            "mode": "content-item-selection",
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

    @property
    @functools.lru_cache()
    def _hypothesis_config(self):
        """
        Return the Hypothesis client config object for the current request.

        See: https://h.readthedocs.io/projects/client/en/latest/publishers/config/#configuring-the-client-using-json

        """
        if not self._context.provisioning_enabled:
            return {}

        api_url = self._request.registry.settings["h_api_url_public"]

        return {
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

    def _grant_token(self, api_url):
        """Return an OAuth 2 the client can use to log in to h."""
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

    @property
    def _is_canvas(self):
        """Return True if Canvas is the LMS that launched us."""
        return (
            self._request.params.get("tool_consumer_info_product_family_code")
            == "canvas"
        )
