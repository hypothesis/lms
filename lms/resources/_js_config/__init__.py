import functools
from enum import Enum
from typing import List, Optional

from lms.content_source import ContentSources, FileDisplayConfig
from lms.models import Assignment, GroupInfo, Grouping, HUser
from lms.services import HAPI, HAPIError
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

        display_config = None

        for content_source in ContentSources.for_family(
            self._request, self._request.product.family
        ):
            if (url_scheme := content_source.url_scheme) and document_url.startswith(
                f"{url_scheme}://"
            ):
                display_config = content_source.get_file_display_config(document_url)
                break

        if not display_config:
            display_config = FileDisplayConfig(
                direct_url=via_url(self._request, document_url)
            )

        # Apply the file display config data to the main data
        if direct_url := display_config.direct_url:
            self._config["viaUrl"] = direct_url
        elif callback := display_config.callback:
            self._config["api"]["viaUrl"] = callback
        else:
            assert False, "This shouldn't happen!"

        if banner := display_config.banner:
            self._config["contentBanner"] = {
                "source": banner.source,
                "itemId": banner.item_id,
            }

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

        # Configure group related settings
        self._configure_groups(course, assignment)

        self._config["rpcServer"] = {
            "allowedOrigins": self._request.registry.settings["rpc_allowed_origins"]
        }
        self._config["debug"]["values"] = self._get_lti_launch_debug_values()

        self._config["editing"] = {
            # Endpoint to get any data needed to get into "editing mode"
            "getConfig": {
                "path": self._request.route_path("lti.reconfigure"),
                "data": self._request.lti_params.serialize(
                    authorization=self.auth_token
                ),
            },
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

        file_picker_config = {
            "formAction": form_action,
            "formFields": form_fields,
            # The "content item selection" that we submit to Canvas's
            # content_item_return_url is actually an LTI launch URL with
            # the selected document URL or file_id as a query parameter. To
            # construct these launch URLs our JavaScript code needs the
            # base URL of our LTI launch endpoint.
            "ltiLaunchUrl": self._request.route_url("lti_launches"),
        }

        # Add specific config for pickers. Ideally we'd only need the relevant
        # ones, but the front-end expects each key. A list here might be good?
        for content_source in ContentSources.get_all(self._request):
            if not content_source.config_key:
                continue

            # We have to include things regardless of family, sadly we can't
            # separate the two things until it's cool to not pass them through
            # to the front end
            if (
                content_source.family
                and content_source.family != self._request.product.family
            ):
                enabled = False
            else:
                enabled = content_source.is_enabled(self._context.application_instance)

            source_config = {"enabled": enabled}
            if enabled:
                source_config.update(
                    content_source.get_picker_config(self._context.application_instance)
                )

            file_picker_config[content_source.config_key] = source_config

        self._config.update(
            {
                "mode": JSConfig.Mode.FILE_PICKER,
                # Info about the product we are currently running in
                "product": self._get_product_info(),
                "filePicker": file_picker_config,
            }
        )
        self._config["debug"]["values"] = self._get_lti_launch_debug_values()
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
                "lms": {
                    "product": self._request.product.family,
                },
                "context_id": self._request.lti_params["context_id"],
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

    def enable_instructor_toolbar(self, enable_editing=False, enable_grading=False):
        """
        Enable the toolbar with controls for instructors in LMS assignments.

        :param enable_editing: Whether to enable controls for editing assignment configuration
        :param enable_grading: Whether to enable grading controls
        """

        if enable_grading:
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
        else:
            students = None

        self._config["instructorToolbar"] = {
            "courseName": self._request.lti_params.get("context_title"),
            "assignmentName": self._request.lti_params.get("resource_link_title"),
            "editingEnabled": enable_editing,
            "gradingEnabled": enable_grading,
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
                self._request.find_service(HAPI).get_user(focused_user).display_name
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
        # The `reportActivity` setting causes the front-end to make a call
        # back to the parent iframe for the specified events. The method in
        # the iframe happens to be called `reportActivity` too, but this is
        # a co-incidence. It could have any name.
        self._hypothesis_client["reportActivity"] = {
            "method": "reportActivity",
            "events": ["create", "update"],
        }

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
            "family": product.family,
            "settings": {
                # Is the small groups feature enabled
                "groupsEnabled": self._request.product.settings.groups_enabled,
            },
            # List of API endpoints we proxy for this product
            "api": {},
        }

        if self._request.product.settings.groups_enabled:
            product_info["api"]["listGroupSets"] = {
                "authUrl": self._request.route_url(product.route.oauth2_authorize),
                "path": self._request.route_path(
                    "api.courses.group_sets.list",
                    course_id=self._request.lti_params["context_id"],
                ),
                "data": {
                    "lms": {
                        "product": self._request.product.family,
                    }
                },
            }

        return product_info

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
        if not self._context.application_instance.provisioning:
            return

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
            self._config["hypothesisClient"]["services"][0][
                "groups"
            ] = "$rpc:requestGroups"

            req = self._request
            self._config["api"]["sync"] = {
                "authUrl": req.route_url(req.product.route.oauth2_authorize),
                "path": req.route_path("api.sync"),
                # This data is consumed by the view in `lms.views.api.sync` which
                # defines the arguments it expects. We need to match that
                # description. Anything we add here should be echoed back by the
                # frontend.
                "data": {
                    "resource_link_id": assignment.resource_link_id,
                    "lms": {
                        "product": self._request.product.family,
                    },
                    "context_id": self._request.lti_params["context_id"],
                    "group_set_id": self._request.product.plugin.grouping.get_group_set_id(
                        self._request, assignment
                    ),
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

    def _get_lti_launch_debug_values(self):
        """Debug values common to different types of LTI launches."""
        ai = self._context.application_instance

        return {
            "Organization ID": ai.organization.public_id if ai.organization else None,
            "Application Instance ID": ai.id,
            "LTI version": ai.lti_version,
        }
