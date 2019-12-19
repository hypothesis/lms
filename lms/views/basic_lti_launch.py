"""
Views for handling what the LTI spec calls "Basic LTI Launches".

A Basic LTI Launch is the form submission POST request that an LMS sends us
when it wants our app to launch an assignment, as opposed to other kinds of
LTI launches such as the Content Item Selection launches that some LMS's
send us while *creating* a new assignment.

The spec requires Basic LTI Launch requests to have an ``lti_message_type``
parameter with the value ``basic-lti-launch-request`` to distinguish them
from other types of launch request (other "message types") but our code
doesn't actually require basic launch requests to have this parameter.
"""

from pyramid.view import view_config, view_defaults

from lms.models import LtiLaunches, ModuleItemConfiguration
from lms.services import HAPIError
from lms.validation import (
    ConfigureModuleItemSchema,
    LaunchParamsSchema,
    LaunchParamsURLConfiguredSchema,
)
from lms.validation.authentication import BearerTokenSchema
from lms.views.helpers import frontend_app, via_url


@view_defaults(
    permission="launch_lti_assignment",
    renderer="lms:templates/basic_lti_launch/basic_lti_launch.html.jinja2",
    request_method="POST",
    route_name="lti_launches",
    schema=LaunchParamsSchema,
)
class BasicLTILaunchViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.context.js_config.update(
            {
                # Configure the front-end mini-app to run.
                "mode": "basic-lti-launch",
                # Add debug information (currently used in the gherkin tests)
                "debug": {
                    "tags": [
                        "role:instructor"
                        if request.lti_user.is_instructor
                        else "role:learner"
                    ]
                },
            }
        )

        if self.is_launched_by_canvas():
            self.initialise_canvas_submission_params()
            self.set_canvas_focused_user()

    def sync_lti_data_to_h(self):
        """
        Sync LTI data to H.

        Before any LTI assignment launch create or update the Hypothesis user
        and group corresponding to the LTI user and course.
        """

        lti_h_service = self.request.find_service(name="lti_h")
        lti_h_service.upsert_h_user()
        lti_h_service.upsert_course_group()
        lti_h_service.add_user_to_group()

    def store_lti_data(self):
        """Store LTI launch data in our LMS database."""

        request = self.request

        # Report all LTI assignment launches to the /reports page.
        LtiLaunches.add(
            request.db,
            request.params.get("context_id"),
            request.params.get("oauth_consumer_key"),
        )

        lti_user = request.lti_user

        # TODO! - The real reason we test for Canvas here is because canvas
        # does not require us to provide student navigation. So we don't need
        # to store this data in the first place.
        if not lti_user.is_instructor and not self.is_launched_by_canvas():
            # Create or update a record of LIS result data for a student launch
            request.find_service(name="lis_result_sourcedid").upsert_from_request(
                request, h_user=self.context.h_user, lti_user=lti_user
            )

    @view_config(canvas_file=True)
    def canvas_file_basic_lti_launch(self):
        """
        Respond to a Canvas file assignment launch.

        Canvas file assignment launch requests have a ``file_id`` request
        parameter, which is the Canvas instance's ID for the file. To display
        the assignment we have to use this ``file_id`` to get a download URL
        for the file from the Canvas API. We then pass that download URL to
        Via. We have to re-do this file-ID-for-download-URL exchange on every
        single launch because Canvas's download URLs are temporary.
        """
        self.sync_lti_data_to_h()
        self.store_lti_data()

        file_id = self.request.params["file_id"]

        self.context.js_config.update(
            {
                # The URL that the JavaScript code will open if it needs the user to
                # authorize us to request a new access token.
                "authUrl": self.request.route_url("canvas_api.authorize"),
                # Set the LMS name to use in user-facing messages.
                "lmsName": "Canvas",
            }
        )

        # Configure the frontend to make a callback to the API to fetch the
        # Via URL.
        self.context.js_config["urls"].update(
            {
                "via_url_callback": self.request.route_url(
                    "canvas_api.files.via_url", file_id=file_id
                )
            }
        )

        self.set_canvas_submission_param("canvas_file_id", file_id)

        return {}

    @view_config(db_configured=True)
    def db_configured_basic_lti_launch(self):
        """
        Respond to a DB-configured assignment launch.

        DB-configured assignment launch requests don't have any kind of file ID
        or document URL in the request. Instead the document URL is stored in
        our own DB. This happens with LMS's that don't support LTI content item
        selection/deep linking, so they don't support storing the document URL
        in the LMS and passing it back to us in each launch request. Instead we
        retrieve the document URL from the DB and pass it to Via.
        """
        self.sync_lti_data_to_h()
        self.store_lti_data()

        frontend_app.configure_grading(self.request, self.context.js_config)

        resource_link_id = self.request.params["resource_link_id"]
        tool_consumer_instance_guid = self.request.params["tool_consumer_instance_guid"]

        # The ``db_configured=True`` view predicate ensures that this view
        # won't be called if there isn't a matching ModuleItemConfiguration in
        # the DB. So here we can safely assume that the ModuleItemConfiguration
        # exists.
        document_url = ModuleItemConfiguration.get_document_url(
            self.request.db, tool_consumer_instance_guid, resource_link_id
        )

        self._set_via_url(document_url)

        return {}

    @view_config(url_configured=True, schema=LaunchParamsURLConfiguredSchema)
    def url_configured_basic_lti_launch(self):
        """
        Respond to a URL-configured assignment launch.

        URL-configured assignment launch requests have the document URL in the
        ``url`` request parameter. This happens in LMS's that support LTI
        content item selection/deep linking: the document URL is chosen during
        content item selection (during assignment creation) and saved in the
        LMS, which passes it back to us in each launch request. All we have to
        do is pass the URL to Via.
        """
        self.sync_lti_data_to_h()
        self.store_lti_data()

        frontend_app.configure_grading(self.request, self.context.js_config)

        url = self.request.parsed_params["url"]
        self._set_via_url(url)

        return {}

    @view_config(
        authorized_to_configure_assignments=True,
        configured=False,
        renderer="lms:templates/file_picker.html.jinja2",
    )
    def unconfigured_basic_lti_launch(self):
        """
        Respond to an unconfigured assignment launch.

        Unconfigured assignment launch requests don't contain any document URL
        or file ID because the assignment's document hasn't been chosen yet.
        This happens in LMS's that don't support LTI content item
        selection/deep linking. They go straight from assignment creation to
        launching the assignment without the user having had a chance to choose
        a document.

        When this happens we show the user our document-selection form instead
        of launching the assignment. The user will choose the document and
        we'll save it in our DB. Subsequent launches of the same assignment
        will then be DB-configured launches rather than unconfigured.
        """

        params = self._extract_lti_params(self.request)

        # Copy the Authorization header as a parameter
        params["authorization"] = BearerTokenSchema(self.request).authorization_param(
            self.request.lti_user
        )

        # Add the config needed by the JavaScript document selection code.
        self.context.js_config.update(
            {
                "mode": "content-item-selection",
                # It is assumed that this view is only used by LMSes for which
                # we do not have an integration with the LMS's file storage.
                # (currently only Canvas supports this).
                "enableLmsFilePicker": False,
                "formAction": self.request.route_url("module_item_configurations"),
                "formFields": params,
                "googleClientId": self.request.registry.settings["google_client_id"],
                "googleDeveloperKey": self.request.registry.settings[
                    "google_developer_key"
                ],
                "customCanvasApiDomain": self.context.custom_canvas_api_domain,
                "lmsUrl": self.context.lms_url,
            }
        )

        return {}

    @classmethod
    def _extract_lti_params(cls, request):
        """Copy all of the LTI params from a request minus OAuth 1 params."""

        # Exclude OAuth 1 variable signing fields as they should not be
        # re-used. If this request needs to be signed, it needs to be signed
        # again.

        return {
            param: value
            for param, value in request.params.items()
            if param not in ["oauth_nonce", "oauth_timestamp", "oauth_signature"]
        }

    # pylint:disable=no-self-use
    @view_config(
        authorized_to_configure_assignments=False,
        configured=False,
        renderer="lms:templates/basic_lti_launch/unconfigured_basic_lti_launch_not_authorized.html.jinja2",
    )
    def unconfigured_basic_lti_launch_not_authorized(self):
        """
        Respond to an unauthorized unconfigured assignment launch.

        This happens when an assignment's document hasn't been chosen yet and
        the assignment is launched by a user who isn't authorized to choose the
        document (for example a learner rather than a teacher). We just show an
        error page.
        """
        return {}

    @view_config(
        authorized_to_configure_assignments=True,
        route_name="module_item_configurations",
        schema=ConfigureModuleItemSchema,
    )
    def configure_module_item(self):
        """
        Respond to a configure module item request.

        This happens after an unconfigured assignment launch. We show the user
        our document selection form instead of launching the assignment, and
        when the user chooses a document and submits the form this is the view
        that receives that form submission.

        We save the chosen document in the DB so that subsequent launches of
        this same assignment will be DB-configured rather than unconfigured.
        And we also send back the assignment launch page, passing the chosen
        URL to Via, as the direct response to the content item form submission.
        """
        document_url = self.request.parsed_params["document_url"]

        ModuleItemConfiguration.set_document_url(
            self.request.db,
            self.request.parsed_params["tool_consumer_instance_guid"],
            self.request.parsed_params["resource_link_id"],
            document_url,
        )

        self._set_via_url(document_url)

        self.sync_lti_data_to_h()
        self.store_lti_data()

        frontend_app.configure_grading(self.request, self.context.js_config)

        return {}

    def _set_via_url(self, document_url):
        """Configure content URL which the frontend will render inside an iframe."""
        self.context.js_config["urls"].update(
            {"via_url": via_url(self.request, document_url)}
        )
        self.set_canvas_submission_param("document_url", document_url)

    # ---------------------------------------------------------------------- #
    # Canvas specific functions

    def is_launched_by_canvas(self):
        return (
            self.request.params.get("tool_consumer_info_product_family_code")
            == "canvas"
        )

    def initialise_canvas_submission_params(self):
        """
        Add config used by frontend to call Canvas `record_submission` API.

        The outcome reporting params are typically only available when
        students (not teachers) launch an assignment.
        """

        lis_result_sourcedid = self.request.params.get("lis_result_sourcedid")
        lis_outcome_service_url = self.request.params.get("lis_outcome_service_url")

        if lis_result_sourcedid and lis_outcome_service_url:
            self.context.js_config["submissionParams"] = {
                "h_username": self.context.h_user.username,
                "lis_result_sourcedid": lis_result_sourcedid,
                "lis_outcome_service_url": lis_outcome_service_url,
            }

    def set_canvas_submission_param(self, name, value):
        """Update config for frontend's calls to `report_submisssion` API."""

        if "submissionParams" in self.context.js_config:
            self.context.js_config["submissionParams"][name] = value

    def set_canvas_focused_user(self):
        """Configure the Hypothesis client to focus on a particular user."""

        # If the launch has been configured to focus on the annotations from
        # a particular user, translate that into Hypothesis client configuration.

        # This parameter is only passed as a part of Canvas SpeedGrader config
        # and is passed as a parameter to a URL which they call us back on.
        focused_user = self.request.params.get("focused_user")
        if not focused_user:
            return

        h_api = self.request.find_service(name="h_api")

        try:
            display_name = h_api.get_user(focused_user).display_name
        except HAPIError:
            # If we couldn't fetch the student's name for any reason, fall back
            # to a placeholder rather than giving up entirely, since the rest
            # of the experience can still work.
            display_name = "(Couldn't fetch student name)"

        # TODO! - Could/should this be replaced with a LISSourcedId lookup?
        self.context.hypothesis_config.update(
            {"focus": {"user": {"username": focused_user, "displayName": display_name}}}
        )
