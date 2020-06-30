import datetime
import functools
from urllib.parse import urlparse

import jwt

from lms.models import GroupInfo, HUser
from lms.services import ConsumerKeyError, HAPIError
from lms.validation.authentication import BearerTokenSchema
from lms.views.helpers import via_url


class JSConfig:  # pylint:disable=too-many-instance-attributes
    """The config for the app's JavaScript code."""

    def __init__(self, context, request):
        self._context = context
        self._request = request
        self._authority = request.registry.settings["h_authority"]
        self._grading_info_service = request.find_service(name="grading_info")
        self._h_api = request.find_service(name="h_api")
        self._lti_user = request.lti_user

    @property
    def _h_user(self):
        return self._lti_user.h_user

    @property
    def _consumer_key(self):
        return self._lti_user.oauth_consumer_key

    @property
    def _ai_getter(self):
        # nb. `ai_getter` service is only available in LTI launches.
        return self._request.find_service(name="ai_getter")

    def add_canvas_file_id(self, canvas_file_id):
        """
        Set the document to the Canvas file with the given canvas_file_id.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing
        """
        self._config["api"]["viaCallbackUrl"] = self._request.route_url(
            "canvas_api.files.via_url", file_id=canvas_file_id
        )
        self._add_canvas_speedgrader_settings(canvas_file_id=canvas_file_id)

    def add_document_url(self, document_url):
        """
        Set the document to the document at the given document_url.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing
        """
        self._config["viaUrl"] = via_url(self._request, document_url)
        self._add_canvas_speedgrader_settings(document_url=document_url)

    def asdict(self):
        """
        Return the configuration for the app's JavaScript code.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing

        :rtype: dict
        """
        return self._config

    def enable_canvas_oauth2_redirect_error_mode(
        self, error_details, is_scope_invalid=False, requested_scopes=None
    ):
        """
        Configure the frontend to show the "Canvas authorization failed" dialog.

        This mini-app is shown when OAuth authorization with Canvas fails
        after redirecting to Canvas's OAuth authorization endpoint.

        :param error_details: Technical details of the error
        :type error_details: str
        :param is_scope_invalid: `True` if authorization failed because the
          OAuth client does not have access to all the necessary scopes
        :type is_scope_invalid: bool
        :param requested_scopes: List of Canvas API scopes that were requested
        :type requested_scopes: list(str)
        """
        self._config.update(
            {
                "mode": "canvas-oauth2-redirect-error",
                "canvasOAuth2RedirectError": {
                    "invalidScope": is_scope_invalid,
                    "errorDetails": error_details,
                    "scopes": requested_scopes or [],
                },
            }
        )

    def enable_lti_launch_mode(self):
        self._config["mode"] = "basic-lti-launch"

        self._config["api"]["sync"] = self._sync_api()

        # The config object for the Hypothesis client.
        # Our JSON-RPC server passes this to the Hypothesis client over
        # postMessage.
        self._config["hypothesisClient"] = self._hypothesis_client

        self._config["rpcServer"] = {
            "allowedOrigins": self._request.registry.settings["rpc_allowed_origins"]
        }

    def enable_content_item_selection_mode(self, form_action, form_fields):
        """
        Put the JavaScript code into "content item selection" mode.

        This mode shows teachers an assignment configuration UI where they can
        choose the document to be annotated for the assignment.

        :param form_action: the HTML `action` attribute for the form that we'll
            use to submit the user's chosen document (the `action` is the URL
            that the form gets submitted to)
        :type form_action: str

        :param form_fields: the fields (keys and values) to include in the
            HTML form that we'll use to submit the user's chosen document
        :type form_fields: dict
        """
        self._config["mode"] = "content-item-selection"

        def google_picker_origin():
            # Pass the URL of the LMS that is launching us to our JavaScript code.
            # When we're being launched in an iframe within the LMS our JavaScript
            # needs to pass this URL (which is the URL of the top-most page) to Google
            # Picker, otherwise Picker refuses to launch inside an iframe.
            return self._context.custom_canvas_api_domain or self._ai_getter.lms_url()

        self._config["filePicker"] = {
            "formAction": form_action,
            "formFields": form_fields,
            "canvas": {
                "enabled": self._canvas_files_available(),
                # The "content item selection" that we submit to Canvas's
                # content_item_return_url is actually an LTI launch URL with
                # the selected document URL or file_id as a query parameter. To
                # construct these launch URLs our JavaScript code needs the
                # base URL of our LTI launch endpoint.
                "ltiLaunchUrl": self._request.route_url("lti_launches"),
                "courseId": self._request.params.get("custom_canvas_course_id"),
            },
            "google": {
                "clientId": self._request.registry.settings["google_client_id"],
                "developerKey": self._request.registry.settings["google_developer_key"],
                "origin": google_picker_origin(),
            },
        }

    def maybe_enable_grading(self):
        """Enable our LMS app's built-in assignment grading UI, if appropriate."""

        if not self._lti_user.is_instructor:
            # Only instructors can grade assignments.
            return

        if "lis_outcome_service_url" not in self._request.params:
            # Only "gradeable" assignments can be graded.
            # Assignments that don't have the lis_outcome_service_url param
            # aren't set as gradeable in the LMS.
            return

        if self._context.is_canvas:
            # Don't show our built-in grader in Canvas because it has its own
            # "SpeedGrader" and we support that instead.
            return

        self._config["grading"] = {
            "enabled": True,
            "courseName": self._request.params.get("context_title"),
            "assignmentName": self._request.params.get("resource_link_title"),
            "students": list(self._get_students()),
        }

    def maybe_set_focused_user(self):
        """
        Configure the Hypothesis client to focus on a particular user.

        If there is a focused_user request param then add the necessary
        Hypothesis client config to get the client to focus on the particular
        user identified by the focused_user param, showing only that user's
        annotations and not others.

        In practice the focused_user param is only ever present in Canvas
        SpeedGrader launches. We add a focused_user query param to the
        SpeedGrader LTI launch URLs that we submit to Canvas for each student
        when the student launches an assignment. Later, Canvas uses these URLs
        to launch us when a teacher grades the assignment in SpeedGrader.

        In theory, though, the focused_user param could work outside of Canvas
        as well if we ever want it to.

        """
        focused_user = self._request.params.get("focused_user")

        if not focused_user:
            return

        self._hypothesis_client["focus"] = {"user": {"username": focused_user}}

        # Unfortunately we need to pass the user's current display name to the
        # Hypothesis client, and we need to make a request to the h API to
        # retrieve that display name.
        try:
            display_name = self._h_api.get_user(focused_user).display_name
        except HAPIError:
            display_name = "(Couldn't fetch student name)"

        self._hypothesis_client["focus"]["user"]["displayName"] = display_name

    def _add_canvas_speedgrader_settings(self, **kwargs):
        """
        Add config used by the JS to call our record_canvas_speedgrader_submission API.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing
        """
        lis_result_sourcedid = self._request.params.get("lis_result_sourcedid")
        lis_outcome_service_url = self._request.params.get("lis_outcome_service_url")

        # Don't set the Canvas submission params in non-Canvas LMS's.
        if not self._context.is_canvas:
            return

        # When a Canvas assignment is launched by a teacher or other
        # non-gradeable user there's no lis_result_sourcedid in the LTI
        # launch params.
        # Don't post submission to Canvas for these cases.
        if not lis_result_sourcedid:
            return

        # When a Canvas assignment isn't gradeable there's no
        # lis_outcome_service_url.
        # Don't post submission to Canvas for these cases.
        if not lis_outcome_service_url:
            return

        self._config["canvas"]["speedGrader"] = {
            "submissionParams": {
                "h_username": self._h_user.username,
                "lis_result_sourcedid": lis_result_sourcedid,
                "lis_outcome_service_url": lis_outcome_service_url,
                "learner_canvas_user_id": self._request.params["custom_canvas_user_id"],
                **kwargs,
            }
        }

    def _auth_token(self):
        """Return the authToken setting."""
        return BearerTokenSchema(self._request).authorization_param(self._lti_user)

    def _canvas_files_available(self):
        """Return True if the Canvas Files API is available to this request."""

        if not self._context.is_canvas:
            return False

        try:
            developer_key = self._ai_getter.developer_key()
        except ConsumerKeyError:
            return False

        return (
            "custom_canvas_course_id" in self._request.params
            and developer_key is not None
        )

    @property
    @functools.lru_cache()
    def _config(self):
        """
        Return the current configuration dict.

        This method populates the default parameters used by all frontend
        apps. The `enable_xxx_mode` methods configures the specific parameters
        needed by a particular frontend mode.

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
        # mutable. You can do self._config["foo"] = "bar" and the mutation will
        # be preserved.

        config = {
            # Settings to do with the API that the backend provides for the
            # frontend to call.
            "api": {
                # The auth token that the JavaScript code will use to
                # authenticate itself to the API.
                "authToken": self._auth_token()
            },
            # The URL that the JavaScript code will open if it needs the user to
            # authorize us to request a new Canvas access token.
            "authUrl": self._request.route_url("canvas_api.authorize"),
            "canvas": {
                # The URL that the JavaScript code will open if it needs the user to
                # authorize us to request a new Canvas access token.
                "authUrl": self._request.route_url("canvas_api.authorize")
            },
            # Some debug information, currently used in the Gherkin tests.
            "debug": {"tags": []},
            # Tell the JavaScript code whether we're in "dev" mode.
            "dev": self._request.registry.settings["dev"],
            # What "mode" to put the JavaScript code in.
            # For example in "basic-lti-launch" mode the JavaScript code
            # launches its BasicLtiLaunchApp, whereas in
            # "content-item-selection" mode it launches its FilePickerApp.
            "mode": None,
        }

        if self._lti_user:
            config["debug"]["tags"].append(
                "role:instructor" if self._lti_user.is_instructor else "role:learner"
            )

        return config

    def _get_students(self):
        """
        Yield the student dicts for the request.

        Yield one student dict for each student who has launched the assignment
        and had grading info recorded for them.
        """
        grading_infos = self._grading_info_service.get_by_assignment(
            oauth_consumer_key=self._consumer_key,
            context_id=self._request.params.get("context_id"),
            resource_link_id=self._request.params.get("resource_link_id"),
        )

        # Yield a "student" dict for each GradingInfo.
        for grading_info in grading_infos:
            h_user = HUser(
                username=grading_info.h_username,
                display_name=grading_info.h_display_name,
            )
            yield {
                "userid": h_user.userid(self._authority),
                "displayName": h_user.display_name,
                "LISResultSourcedId": grading_info.lis_result_sourcedid,
                "LISOutcomeServiceUrl": grading_info.lis_outcome_service_url,
            }

    def _grant_token(self, api_url):
        """Return an OAuth 2 grant token the client can use to log in to h."""
        now = datetime.datetime.utcnow()

        claims = {
            "aud": urlparse(api_url).hostname,
            "iss": self._request.registry.settings["h_jwt_client_id"],
            "sub": self._h_user.userid(self._authority),
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

        if not self._ai_getter.provisioning_enabled():
            return {}

        api_url = self._request.registry.settings["h_api_url_public"]

        return {
            # For documentation of these Hypothesis client settings see:
            # https://h.readthedocs.io/projects/client/en/latest/publishers/config/#configuring-the-client-using-json
            "services": [
                {
                    "allowLeavingGroups": False,
                    "apiUrl": api_url,
                    "authority": self._authority,
                    "enableShareLinks": False,
                    "grantToken": self._grant_token(api_url),
                    "groups": self._groups(),
                }
            ]
        }

    def _groups(self):
        if self._context.canvas_sections_enabled:
            return "$rpc:requestGroups"
        return [self._context.h_group.groupid(self._authority)]

    def _sync_api(self):
        if not self._context.canvas_sections_enabled:
            return None

        req = self._request

        sync_api_config = {
            "path": req.route_path("canvas_api.sync"),
            "data": {
                "lms": {
                    "tool_consumer_instance_guid": req.params[
                        "tool_consumer_instance_guid"
                    ]
                },
                "course": {
                    "context_id": req.params["context_id"],
                    "custom_canvas_course_id": req.params["custom_canvas_course_id"],
                },
                "group_info": {
                    key: value
                    for key, value in req.params.items()
                    if key in GroupInfo.columns()
                },
            },
        }

        if "learner_canvas_user_id" in req.params:
            sync_api_config["data"]["learner"] = {
                "canvas_user_id": req.params["learner_canvas_user_id"]
            }

        return sync_api_config
