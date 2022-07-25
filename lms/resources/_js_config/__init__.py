import functools
from enum import Enum
from typing import List, Optional

from lms.models import Assignment, GroupInfo, Grouping, HUser
from lms.product import Product
from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.resources._js_config.file_picker_config import FilePickerConfig
from lms.services import HAPIError, JSTORService, VitalSourceService
from lms.validation.authentication import BearerTokenSchema
from lms.views.helpers import via_url


class JSConfig:
    """The config for the app's JavaScript code."""

    class Mode(str, Enum):
        OAUTH2_REDIRECT_ERROR = "oauth2-redirect-error"
        BASIC_LTI_LAUNCH = "basic-lti-launch"
        FILE_PICKER = "content-item-selection"
        ERROR_DIALOG = "error-dialog"

    class ErrorCode(str, Enum):
        BLACKBOARD_MISSING_INTEGRATION = "blackboard_missing_integration"
        CANVAS_INVALID_SCOPE = "canvas_invalid_scope"
        REUSED_CONSUMER_KEY = "reused_consumer_key"

    def __init__(self, context, request):
        self._context = context
        self._request = request
        self._authority = request.registry.settings["h_authority"]
        self._grading_info_service = request.find_service(name="grading_info")
        self._lti_user = request.lti_user

    @property
    def _h_user(self):
        return self._lti_user.h_user

    def add_document_url(self, document_url):
        """
        Set the document to the document at the given document_url.

        This configures the frontend to inject the Via iframe with this URL as
        its src immediately, without making any further API requests to get the
        Via URL.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing
        """
        jstor_service = self._request.find_service(iface=JSTORService)

        if document_url.startswith("blackboard://"):
            self._config["api"]["viaUrl"] = {
                "authUrl": self._request.route_url(Blackboard.route.oauth2_authorize),
                "path": self._request.route_path(
                    "blackboard_api.files.via_url",
                    course_id=self._request.lti_params["context_id"],
                    _query={"document_url": document_url},
                ),
            }
        elif document_url.startswith("canvas://"):
            self._config["api"]["viaUrl"] = {
                "authUrl": self._request.route_url(Canvas.route.oauth2_authorize),
                "path": self._request.route_path(
                    "canvas_api.files.via_url",
                    resource_link_id=self._request.lti_params["resource_link_id"],
                ),
            }
        elif document_url.startswith("vitalsource://"):
            svc = self._request.find_service(VitalSourceService)

            # nb. VitalSource doesn't use Via, but is otherwise handled exactly
            # the same way by the frontend.
            self._config["viaUrl"] = svc.get_launch_url(
                user_reference=self._request.lti_params[svc.user_lti_param],
                document_url=document_url,
            )
        elif jstor_service.enabled and document_url.startswith("jstor://"):
            self._config["viaUrl"] = jstor_service.via_url(self._request, document_url)
        else:
            self._config["viaUrl"] = via_url(self._request, document_url)

    def asdict(self):
        """
        Return the configuration for the app's JavaScript code.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing

        :rtype: dict
        """
        return self._config

    def enable_oauth2_redirect_error_mode(
        self,
        auth_route: str,
        error_code=None,
        error_details: Optional[dict] = None,
        canvas_scopes: List[str] = None,
    ):
        """
        Configure the frontend to show the "Authorization failed" dialog.

        This is shown when authorizing with a third-party OAuth API like the
        Canvas API or the Blackboard API fails after the redirect to the
        third-party authorization endpoint.

        :param error_code: Code identifying a particular error
        :param error_details: JSON-serializable technical details about the error
        :param auth_route: route for the "Try again" button in the dialog
        :param canvas_scopes: List of scopes that were requested
        """
        if self._lti_user:
            bearer_token = BearerTokenSchema(self._request).authorization_param(
                self._lti_user
            )
            auth_url = self._request.route_url(
                auth_route,
                _query=[("authorization", bearer_token)],
            )
        else:
            auth_url = None

        self._config.update(
            {
                "mode": JSConfig.Mode.OAUTH2_REDIRECT_ERROR,
                "OAuth2RedirectError": {
                    "authUrl": auth_url,
                    "errorCode": error_code,
                    "canvasScopes": canvas_scopes or [],
                },
            }
        )

        if error_details:
            self._config["OAuth2RedirectError"]["errorDetails"] = error_details

    def enable_error_dialog_mode(self, error_code, error_details=None):
        self._config.update(
            {
                "mode": JSConfig.Mode.ERROR_DIALOG,
                "errorDialog": {"errorCode": error_code},
            }
        )

        if error_details:
            self._config["errorDialog"]["errorDetails"] = error_details

    def enable_lti_launch_mode(self, assignment: Assignment):
        """
        Put the JavaScript code into "LTI launch" mode.

        This mode launches an assignment.
        """
        self._config["mode"] = JSConfig.Mode.BASIC_LTI_LAUNCH

        self._config["api"]["sync"] = self._sync_api(assignment)

        # The config object for the Hypothesis client.
        # Our JSON-RPC server passes this to the Hypothesis client over
        # postMessage.
        self._config["hypothesisClient"] = self._hypothesis_client

        self._config["rpcServer"] = {
            "allowedOrigins": self._request.registry.settings["rpc_allowed_origins"]
        }

    def enable_file_picker_mode(self, form_action, form_fields):
        """
        Put the JavaScript code into "file picker" mode.

        This mode shows teachers an assignment configuration UI where they can
        choose the document to be annotated for the assignment.

        :param form_action: the HTML `action` attribute for the URL that we'll
            submit the user's chosen document to
        :param form_fields: the fields (keys and values) to include in the
            HTML form that we submit
        """

        args = self._request, self._context.application_instance

        self._config.update(
            {
                "mode": JSConfig.Mode.FILE_PICKER,
                "filePicker": {
                    "formAction": form_action,
                    "formFields": form_fields,
                    # The "content item selection" that we submit to Canvas's
                    # content_item_return_url is actually an LTI launch URL with
                    # the selected document URL or file_id as a query parameter. To
                    # construct these launch URLs our JavaScript code needs the
                    # base URL of our LTI launch endpoint.
                    "ltiLaunchUrl": self._request.route_url("lti_launches"),
                    # Specific config for pickers
                    "blackboard": FilePickerConfig.blackboard_config(*args),
                    "canvas": FilePickerConfig.canvas_config(*args),
                    "google": FilePickerConfig.google_files_config(*args),
                    "microsoftOneDrive": FilePickerConfig.microsoft_onedrive(*args),
                    "vitalSource": FilePickerConfig.vitalsource_config(*args),
                    "jstor": FilePickerConfig.jstor_config(*args),
                },
            }
        )

    def add_deep_linking_api(self):
        """
        Add the details of the "DeepLinking API" in LMS where we support deep linking.

        This API will be used by the frontend to retrieve the form fields required
        for the deep linking submission while on FILE_PICKER mode to store the
        selected content on the LMS.
        """
        config = {
            "path": self._request.route_path("lti.v11.deep_linking.form_fields"),
            "data": {
                "content_item_return_url": self._request.lti_params[
                    "content_item_return_url"
                ],
            },
        }
        if self._context.application_instance.lti_version == "1.3.0":
            config["path"] = self._request.route_path(
                "lti.v13.deep_linking.form_fields"
            )
            config["data"]["deep_linking_settings"] = self._request.lti_params.get(
                "deep_linking_settings"
            )

        self._config.setdefault("filePicker", {})
        self._config["filePicker"]["deepLinkingAPI"] = config

    def enable_grading_bar(self):
        """Enable our LMS app's built-in assignment grading UI."""

        # Get one student dict for each student who has launched the assignment
        # and had grading info recorded for them.
        students = []

        grading_infos = self._grading_info_service.get_by_assignment(
            application_instance=self._context.application_instance,
            context_id=self._request.lti_params.get("context_id"),
            resource_link_id=self._request.lti_params.get("resource_link_id"),
        )

        for grading_info in grading_infos:
            h_user = HUser(
                username=grading_info.h_username,
                display_name=grading_info.h_display_name,
            )
            students.append(
                {
                    "userid": h_user.userid(self._authority),
                    "displayName": h_user.display_name,
                    "lmsId": grading_info.user_id,
                    "LISResultSourcedId": grading_info.lis_result_sourcedid,
                    # We are using the value from the request instead of the one stored in GradingInfo.
                    # This allows us to still read and submit grades when something in the LMS changes.
                    # For example in LTI version upgrades, the endpoint is likely to change as we move from
                    # LTI 1.1 basic outcomes API to LTI1.3's Assignment and Grade Services.
                    # Also when the install's domain is updated all the records in the DB will be outdated.
                    "LISOutcomeServiceUrl": self._request.lti_params[
                        "lis_outcome_service_url"
                    ],
                }
            )

        self._config["grading"] = {
            "enabled": True,
            "courseName": self._request.lti_params.get("context_title"),
            "assignmentName": self._request.lti_params.get("resource_link_title"),
            "students": students,
        }

    def set_focused_user(self, focused_user):
        """Configure the client to only show one users' annotations."""
        self._hypothesis_client["focus"] = {"user": {"username": focused_user}}

        # Unfortunately we need to pass the user's current display name to the
        # Hypothesis client, and we need to make a request to the h API to
        # retrieve that display name.
        try:
            display_name = (
                self._request.find_service(name="h_api")
                .get_user(focused_user)
                .display_name
            )
        except HAPIError:
            display_name = "(Couldn't fetch student name)"

        self._hypothesis_client["focus"]["user"]["displayName"] = display_name

    def add_canvas_speedgrader_settings(self, document_url):
        """
        Add config for students to record submissions with Canvas Speedgrader.

        This adds the config to call our `record_canvas_speedgrader_submission`
        API.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing
        """
        lti_params = self._request.lti_params

        self._config["canvas"]["speedGrader"] = {
            "submissionParams": {
                "h_username": self._h_user.username,
                "group_set": self._request.params.get("group_set"),
                "document_url": document_url,
                # Canvas doesn't send the right value for this on speed grader launches
                # sending instead the same value as for "context_id"
                "resource_link_id": lti_params.get("resource_link_id"),
                "lis_result_sourcedid": lti_params["lis_result_sourcedid"],
                "lis_outcome_service_url": lti_params["lis_outcome_service_url"],
                "learner_canvas_user_id": lti_params["custom_canvas_user_id"],
            },
        }

        # Enable the LMS frontend to receive notifications on annotation activity
        # We'll use this information to only send the submission to canvas on first annotation.
        if self._request.feature("submit_on_annotation"):
            # The `reportActivity` setting causes the front-end to make a call
            # back to the parent iframe for the specified events. The method in
            # the iframe happens to be called `reportActivity` too, but this is
            # a co-incidence. It could have any name.
            self._hypothesis_client["reportActivity"] = {
                "method": "reportActivity",
                "events": ["create", "update"],
            }

    def _auth_token(self):
        """Return the authToken setting."""
        return BearerTokenSchema(self._request).authorization_param(self._lti_user)

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
            "canvas": {},
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

        if not self._context.application_instance.provisioning:
            return {}

        api_url = self._request.registry.settings["h_api_url_public"]

        # Generate a short-lived login token for the Hypothesis client.
        grant_token_svc = self._request.find_service(name="grant_token")
        grant_token = grant_token_svc.generate_token(self._h_user)

        return {
            # For documentation of these Hypothesis client settings see:
            # https://h.readthedocs.io/projects/client/en/latest/publishers/config/#configuring-the-client-using-json
            "services": [
                {
                    "allowFlagging": False,
                    "allowLeavingGroups": False,
                    "apiUrl": api_url,
                    "authority": self._authority,
                    "enableShareLinks": False,
                    "grantToken": grant_token,
                    "groups": self._groups(),
                }
            ]
        }

    def _groups(self):
        if self._context.grouping_type == Grouping.Type.COURSE:
            return [self._context.course.groupid(self._authority)]

        # If not using the default COURSE grouping point the FE
        # to the sync API to dynamically get the relevant groupings.
        return "$rpc:requestGroups"

    def _sync_api(self, assignment):
        """Add configuration the front-end will use to get groupings."""

        if self._context.grouping_type == Grouping.Type.COURSE:
            return None

        req = self._request

        return {
            "authUrl": req.route_url(req.product.route.oauth2_authorize),
            "path": req.route_path("api.sync"),
            # This data is consumed by the view in `lms.views.api.sync` which
            # defines the arguments it expects. We need to match that
            # description. Anything we add here should be echoed back by the
            # frontend.
            "data": {
                "assignment_id": assignment.id,
                "lms": {
                    "product": self._request.product.family,
                },
                "context_id": self._request.lti_params["context_id"],
                "group_set_id": self._context.group_set_id,
                "group_info": {
                    key: value
                    for key, value in self._request.lti_params.items()
                    if key in GroupInfo.columns()
                },
                # The student we are currently grading. In the case of Canvas
                # this will be present in the SpeedGrader launch URL and
                # available at launch time. When using our own grading bar this
                # will be passed by the frontend
                "gradingStudentId": req.params.get("learner_canvas_user_id"),
            },
        }
