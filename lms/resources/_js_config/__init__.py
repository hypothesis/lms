import functools
import re
from enum import Enum
from typing import Any

from lms.error_code import ErrorCode
from lms.events import LTIEvent
from lms.js_config_types import DashboardConfig, DashboardRoutes
from lms.models import Assignment, Course, Grouping
from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.d2l import D2L
from lms.resources._js_config.file_picker_config import FilePickerConfig
from lms.services import HAPI, EventService, HAPIError, JSTORService, VitalSourceService
from lms.validation.authentication import BearerTokenSchema
from lms.views.helpers import via_url


class JSConfig:
    """The config for the app's JavaScript code."""

    class Mode(str, Enum):
        OAUTH2_REDIRECT_ERROR = "oauth2-redirect-error"
        BASIC_LTI_LAUNCH = "basic-lti-launch"
        FILE_PICKER = "content-item-selection"
        ERROR_DIALOG = "error-dialog"
        DASHBOARD = "dashboard"

    ErrorCode = ErrorCode
    """Exposing error codes here for convenience for clients."""

    def __init__(self, _context, request):
        self._request = request
        self._authority = request.registry.settings["h_authority"]
        self._lti_user = request.lti_user

    @property
    def _h_user(self):
        return self._lti_user.h_user

    @property
    def _application_instance(self):
        return self._lti_user.application_instance

    def add_document_url(  # pylint: disable=too-complex,too-many-branches,useless-suppression  # noqa: C901, PLR0912
        self, document_url
    ) -> None:
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
        elif document_url.startswith("canvas://file"):
            self._config["api"]["viaUrl"] = {
                "authUrl": self._request.route_url(Canvas.route.oauth2_authorize),
                "path": self._request.route_path(
                    "canvas_api.files.via_url",
                    resource_link_id=self._request.lti_params["resource_link_id"],
                ),
            }

        elif document_url.startswith("canvas://page"):
            self._config["api"]["viaUrl"] = {
                "authUrl": self._request.route_url(Canvas.route.oauth2_authorize),
                "path": self._request.route_path("canvas_api.pages.via_url"),
            }

        elif document_url.startswith("canvas-studio://media"):
            self._config["api"]["viaUrl"] = {
                "authUrl": self._request.route_url("canvas_studio_api.oauth.authorize"),
                "path": self._request.route_path("canvas_studio_api.via_url"),
            }

        elif document_url.startswith("d2l://"):
            self._config["api"]["viaUrl"] = {
                "authUrl": self._request.route_url(D2L.route.oauth2_authorize),
                "path": self._request.route_path(
                    "d2l_api.courses.files.via_url",
                    course_id=self._request.lti_params["context_id"],
                    _query={"document_url": document_url},
                ),
            }

        elif document_url.startswith("moodle://file"):
            self._config["api"]["viaUrl"] = {
                "authUrl": None,
                "path": self._request.route_path(
                    "moodle_api.courses.files.via_url",
                    course_id=self._request.lti_params["context_id"],
                    _query={"document_url": document_url},
                ),
            }
        elif document_url.startswith("moodle://page"):
            self._config["api"]["viaUrl"] = {
                "authUrl": None,
                "path": self._request.route_path("moodle_api.pages.via_url"),
            }

        elif document_url.startswith("vitalsource://"):
            svc: VitalSourceService = self._request.find_service(VitalSourceService)

            if svc.sso_enabled:
                # nb. VitalSource doesn't use Via, but is otherwise handled
                # exactly the same way by the frontend.
                self._config["api"]["viaUrl"] = {
                    "path": self._request.route_url(
                        "vitalsource_api.launch_url",
                        _query={
                            "user_reference": svc.get_user_reference(
                                self._request.lti_params
                            ),
                            "document_url": document_url,
                        },
                    )
                }
            else:
                # This looks a bit silly, but pretty soon the above will
                # be setting `api.viaURL` not `viaURL`
                self._config["viaUrl"] = svc.get_book_reader_url(
                    document_url=document_url
                )

            content_config = svc.get_client_focus_config(document_url)
            if content_config:
                self._update_focus_config(content_config)

        elif jstor_service.enabled and document_url.startswith("jstor://"):
            self._config["viaUrl"] = jstor_service.via_url(self._request, document_url)
            self._config["contentBanner"] = {
                "source": "jstor",
                "itemId": document_url.replace("jstor://", ""),
            }
        else:
            self._config["viaUrl"] = via_url(self._request, document_url)

    def _update_focus_config(self, updates: dict):
        """
        Update the `focus` dict in the Hypothesis client's configuration.

        This configures the client to filter annotations based on a selected
        user, page range etc.
        """
        focus_config = self._hypothesis_client.setdefault("focus", {})
        focus_config.update(updates)

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
        error_details: dict | None = None,
        canvas_scopes: list[str] | None = None,
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
            auth_url = self._request.route_url(
                auth_route,
                _query=[("authorization", self.auth_token)],
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

    def enable_error_dialog_mode(self, error_code, error_details=None, message=None):
        self._config.update(
            {
                "mode": JSConfig.Mode.ERROR_DIALOG,
                "errorDialog": {"errorCode": error_code},
            }
        )

        if error_details:
            self._config["errorDialog"]["errorDetails"] = error_details

        if message:
            self._config["errorDialog"]["errorMessage"] = message

        EventService.queue_event(
            LTIEvent.from_request(
                request=self._request,
                type_=LTIEvent.Type.ERROR_CODE,
                data={"code": error_code} | (error_details or {}),
            )
        )

    def enable_dashboard_mode(self):
        self._config.update(
            {
                "mode": JSConfig.Mode.DASHBOARD,
                "dashboard": DashboardConfig(
                    routes=DashboardRoutes(
                        assignment=self._to_frontend_template(
                            "dashboard.api.assignment"
                        ),
                        assignment_stats=self._to_frontend_template(
                            "dashboard.api.assignment.stats"
                        ),
                        course=self._to_frontend_template("dashboard.api.course"),
                        course_assignment_stats=self._to_frontend_template(
                            "dashboard.api.course.assignments.stats"
                        ),
                    ),
                ),
            }
        )

    def enable_lti_launch_mode(self, course, assignment: Assignment):
        """
        Put the JavaScript code into "LTI launch" mode.

        This mode launches an assignment.
        """
        self._config["mode"] = JSConfig.Mode.BASIC_LTI_LAUNCH
        # Info about the product we are currently running in
        self._config["product"] = self._get_product_info()

        # The config object for the Hypothesis client.
        # Our JSON-RPC server passes this to the Hypothesis client over
        # postMessage.
        self._config["hypothesisClient"] = self._hypothesis_client

        self._config["hypothesisClient"]["annotationMetadata"] = (
            self._generate_annotation_metadata(assignment)
        )

        # Configure group related settings
        self._configure_groups(course, assignment)

        self._config["rpcServer"] = {
            "allowedOrigins": self._request.registry.settings["rpc_allowed_origins"]
        }
        self._config["debug"]["values"] = self._get_lti_launch_debug_values(
            course, assignment
        )

        self._config["editing"] = {
            # Endpoint to get any data needed to get into "editing mode"
            "getConfig": {
                "path": self._request.route_path("lti.reconfigure"),
                "data": self._request.lti_params.serialize(
                    authorization=self.auth_token
                ),
            },
        }

    def enable_file_picker_mode(  # noqa: PLR0913
        self,
        form_action,
        form_fields,
        course: Course,
        assignment: Assignment | None = None,
        prompt_for_title=False,
    ):
        """
        Put the JavaScript code into "file picker" mode.

        This mode shows teachers an assignment configuration UI where they can
        choose the document to be annotated for the assignment.

        :param form_action: the HTML `action` attribute for the URL that we'll
            submit the user's chosen document to
        :param form_fields: the fields (keys and values) to include in the
            HTML form that we submit
        :param course: Currently active course
        :param assignment: Currently active assignment
        :param prompt_for_title: Whether or not to prompt for a title while configuring the assignment
        """

        args = self._request, self._application_instance

        self._config.update(
            {
                "mode": JSConfig.Mode.FILE_PICKER,
                # Info about the product we are currently running in
                "product": self._get_product_info(),
                "filePicker": {
                    "formAction": form_action,
                    "formFields": form_fields,
                    "promptForTitle": prompt_for_title,
                    # The "content item selection" that we submit to Canvas's
                    # content_item_return_url is actually an LTI launch URL with
                    # the selected document URL or file_id as a query parameter. To
                    # construct these launch URLs our JavaScript code needs the
                    # base URL of our LTI launch endpoint.
                    "ltiLaunchUrl": self._request.route_url("lti_launches"),
                    # Specific config for pickers
                    "blackboard": FilePickerConfig.blackboard_config(*args),
                    "d2l": FilePickerConfig.d2l_config(*args),
                    "moodle": FilePickerConfig.moodle_config(*args),
                    "canvas": FilePickerConfig.canvas_config(*args),
                    "canvasStudio": FilePickerConfig.canvas_studio_config(*args),
                    "google": FilePickerConfig.google_files_config(*args),
                    "microsoftOneDrive": FilePickerConfig.microsoft_onedrive(*args),
                    "vitalSource": FilePickerConfig.vitalsource_config(*args),
                    "jstor": FilePickerConfig.jstor_config(*args),
                    "youtube": FilePickerConfig.youtube_config(*args),
                },
            }
        )
        self._config["debug"]["values"] = self._get_lti_launch_debug_values(
            course, assignment
        )
        return self._config

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
                "context_id": self._request.lti_params["context_id"],
            },
        }
        if self._application_instance.lti_version == "1.3.0":
            config["path"] = self._request.route_path(
                "lti.v13.deep_linking.form_fields"
            )
            config["data"]["opaque_data_lti13"] = self._request.lti_params.get(
                "deep_linking_settings"
            )
        else:
            config["data"]["opaque_data_lti11"] = self._request.lti_params.get("data")

        self._config.setdefault("filePicker", {})
        self._config["filePicker"]["deepLinkingAPI"] = config

    def enable_instructor_dashboard_entry_point(self, assignment):
        self._hypothesis_client["dashboard"] = {
            "showEntryPoint": True,
            "authTokenRPCMethod": "requestAuthToken",
            "entryPointURL": self._request.route_url(
                "dashboard.launch.assignment", assignment_id=assignment.id
            ),
            "authFieldName": "authorization",
        }
        self._config["hypothesisClient"] = self._hypothesis_client

    def enable_toolbar_editing(self):
        toolbar_config = self._get_toolbar_config()

        toolbar_config["editingEnabled"] = True
        self._config["instructorToolbar"] = toolbar_config

    def enable_toolbar_grading(self, students, score_maximum=None):
        toolbar_config = self._get_toolbar_config()

        toolbar_config["gradingEnabled"] = True
        toolbar_config["acceptGradingComments"] = (
            self._request.product.plugin.misc.accept_grading_comments(
                self._application_instance
            )
        )
        toolbar_config["students"] = students
        toolbar_config["scoreMaximum"] = score_maximum

        self._config["instructorToolbar"] = toolbar_config

    def _get_toolbar_config(self):
        toolbar_config = self._config.get("instructorToolbar", {})
        toolbar_config.setdefault(
            "courseName", self._request.lti_params.get("context_title")
        )
        toolbar_config.setdefault(
            "assignmentName", self._request.lti_params.get("resource_link_title")
        )
        return toolbar_config

    def set_focused_user(self, focused_user):
        """Configure the client to only show one users' annotations while an instructor is in SpeedGrader."""
        # Unfortunately we need to pass the user's current display name to the
        # Hypothesis client, and we need to make a request to the h API to
        # retrieve that display name.
        try:
            display_name = (
                self._request.find_service(HAPI).get_user(focused_user).display_name
            )
        except HAPIError:
            display_name = "(Couldn't fetch student name)"

        self._update_focus_config(
            {
                "user": {
                    "username": focused_user,
                    "displayName": display_name,
                }
            }
        )

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
        # The `reportActivity` setting causes the front-end to make a call
        # back to the parent iframe for the specified events. The method in
        # the iframe happens to be called `reportActivity` too, but this is
        # a co-incidence. It could have any name.
        self._hypothesis_client["reportActivity"] = {
            "method": "reportActivity",
            "events": ["create", "update"],
        }

    def enable_client_feature(self, feature: str):
        """
        Enable a feature flag in the client.

        The effective set of enabled feature flags is the union of flags enabled
        via this method and flags enabled for the H user.

        :param feature: A feature flag to enable.
        """
        current_features: list[str] = self._hypothesis_client.setdefault("features", [])
        if feature not in current_features:
            current_features.append(feature)

    @property
    def auth_token(self):
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
                "authToken": self.auth_token
            },
            "canvas": {},
            "debug": {
                # Some debug information, currently used in the Gherkin tests.
                "tags": [],
                # Info dumped to the console to help support.
                "values": {},
            },
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

    def _get_product_info(self):
        """Return product (Canvas, BB, D2L..) configuration."""
        product = self._request.product

        product_info = {
            "settings": {
                # Is the small groups feature enabled
                "groupsEnabled": self._request.product.settings.groups_enabled,
            },
            # List of API endpoints we proxy for this product
            "api": {},
        }

        if self._request.product.settings.groups_enabled:
            product_info["api"]["listGroupSets"] = {
                "authUrl": (
                    self._request.route_url(product.route.oauth2_authorize)
                    if product.route.oauth2_authorize
                    else None
                ),
                "path": self._request.route_path(
                    "api.courses.group_sets.list",
                    course_id=self._request.lti_params["context_id"],
                ),
            }

        return product_info

    @property
    @functools.lru_cache()
    def _hypothesis_client(self) -> dict[str, Any]:
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
        api_url = self._request.registry.settings["h_api_url_public"]

        # Generate a short-lived login token for the Hypothesis client.
        grant_token_svc = self._request.find_service(name="grant_token")
        grant_token = grant_token_svc.generate_token(self._h_user)

        return {
            # For documentation of these Hypothesis client settings see:
            # https://h.readthedocs.io/projects/client/en/latest/publishers/config.html#configuring-the-client-using-json
            "services": [
                {
                    "allowFlagging": False,
                    "allowLeavingGroups": False,
                    "apiUrl": api_url,
                    "authority": self._authority,
                    "enableShareLinks": False,
                    "grantToken": grant_token,
                }
            ]
        }

    def _configure_groups(self, course, assignment):
        """Configure how the client will fetch groups when in LAUNCH mode."""
        grouping_type = self._request.find_service(
            name="grouping"
        ).get_launch_grouping_type(self._request, course, assignment)

        if grouping_type == Grouping.Type.COURSE:
            self._config["hypothesisClient"]["services"][0]["groups"] = [
                course.groupid(self._authority)
            ]
            self._config["api"]["sync"] = None

        else:
            # If not using the default COURSE grouping point the FE
            # to the sync API to dynamically get the relevant groupings.
            self._config["hypothesisClient"]["services"][0]["groups"] = (
                "$rpc:requestGroups"
            )

            req = self._request
            self._config["api"]["sync"] = {
                "authUrl": (
                    req.route_url(req.product.route.oauth2_authorize)
                    if req.product.route.oauth2_authorize
                    else None
                ),
                "path": req.route_path("api.sync"),
                # This data is consumed by the view in `lms.views.api.sync` which
                # defines the arguments it expects. We need to match that
                # description. Anything we add here should be echoed back by the
                # frontend.
                "data": {
                    "resource_link_id": assignment.resource_link_id,
                    "context_id": self._request.lti_params["context_id"],
                    "group_set_id": self._request.product.plugin.grouping.get_group_set_id(
                        self._request, assignment, historical_assignment=None
                    ),
                    "group_info": {
                        key: value
                        for key, value in self._request.lti_params.items()
                        if key
                        in [
                            # Most (all) of these are duplicated elsewhere, we'll keep updating for now
                            # because external analytics query rely on this table.
                            "context_id",
                            "context_title",
                            "context_label",
                            "tool_consumer_info_product_family_code",
                            "tool_consumer_info_version",
                            "tool_consumer_instance_name",
                            "tool_consumer_instance_description",
                            "tool_consumer_instance_url",
                            "tool_consumer_instance_contact_email",
                            "tool_consumer_instance_guid",
                            "custom_canvas_api_domain",
                            "custom_canvas_course_id",
                        ]
                    },
                    # The student we are currently grading. In the case of Canvas
                    # this will be present in the SpeedGrader launch URL and
                    # available at launch time. When using our own grading bar this
                    # will be passed by the frontend
                    "gradingStudentId": req.params.get("learner_canvas_user_id"),
                },
            }

    def _get_lti_launch_debug_values(
        self, course: Course, assignment: Assignment | None
    ):
        """Debug values common to different types of LTI launches."""
        ai = self._application_instance

        return {
            "Organization ID": ai.organization.public_id if ai.organization else None,
            "Application Instance ID": ai.id,
            "Assignment ID": assignment.id if assignment else None,
            "Course ID": course.id,
            "LTI version": ai.lti_version,
        }

    def _generate_annotation_metadata(self, assignment):
        return {
            "lms": {
                "guid": self._application_instance.tool_consumer_instance_guid,
                "assignment": {
                    "resource_link_id": assignment.resource_link_id,
                },
            },
        }

    def _to_frontend_template(self, route_name):
        """Convert a route pattern like /path/path/{parameter} to /path/path/:parameter."""
        route = self._request.registry.introspector.get("routes", route_name)
        pattern = route["pattern"]

        return re.sub(r"{([^}]+)}", r":\1", pattern)
