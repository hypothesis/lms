from datetime import datetime

from pyramid.view import view_config, view_defaults

from lms.models import LtiLaunches, ModuleItemConfiguration
from lms.services.lti_hypothesis_bridge import LTIHypothesisBridge
from lms.validation import (
    LaunchParamsURLConfiguredSchema,
    LISResultSourcedIdSchema,
    ValidationError,
)
from lms.validation.authentication import BearerTokenSchema
from lms.views.helpers import frontend_app
from lms.views.lti import LTIViewBaseClass


@view_defaults(route_name="lti_launches",)
class BasicLTILaunchViews(LTIViewBaseClass):
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

        self._report_to_h(self.context, self.request)

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

        self._set_submission_param("canvas_file_id", file_id)

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
        self._report_to_h(self.context, self.request)

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
        self._report_to_h(self.context, self.request)

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
        oauth_consumer_key = self.request.lti_user.oauth_consumer_key

        # Add the config needed by the JavaScript document selection code.
        self.context.js_config.update(
            {
                "mode": "content-item-selection",
                # It is assumed that this view is only used by LMSes for which
                # we do not have an integration with the LMS's file storage.
                # (currently only Canvas supports this).
                "enableLmsFilePicker": False,
                "formAction": self.request.route_url("module_item_configurations"),
                "formFields": {
                    "authorization": BearerTokenSchema(
                        self.request
                    ).authorization_param(self.request.lti_user),
                    "resource_link_id": self.request.params["resource_link_id"],
                    "tool_consumer_instance_guid": self.request.params[
                        "tool_consumer_instance_guid"
                    ],
                    "oauth_consumer_key": oauth_consumer_key,
                    "user_id": self.request.lti_user.user_id,
                    "context_id": self.request.params["context_id"],
                },
                "googleClientId": self.request.registry.settings["google_client_id"],
                "googleDeveloperKey": self.request.registry.settings[
                    "google_developer_key"
                ],
                "customCanvasApiDomain": self.context.custom_canvas_api_domain,
                "lmsUrl": self.context.lms_url,
            }
        )

        return {}

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

    @classmethod
    def _report_to_h(cls, context, request):
        """
        Update H with all the required information.

        TODO! - What is this really up to? All sorts. Think of a better name
        """

        # Before any LTI assignment launch create or update the Hypothesis user
        # and group corresponding to the LTI user and course.
        LTIHypothesisBridge.upsert_h_user(context, request)
        LTIHypothesisBridge.upsert_course_group(context, request)
        LTIHypothesisBridge.add_user_to_group(context, request)

        cls._report_lti_launch(request)
        cls._upsert_lis_result_sourcedid(context, request)

    @classmethod
    def _report_lti_launch(cls, request):
        # Report an LTI launch to the /reports page.
        request.db.add(
            LtiLaunches(
                context_id=request.params.get("context_id"),
                lti_key=request.params.get("oauth_consumer_key"),
                created=datetime.utcnow(),
            )
        )

    @classmethod
    def _upsert_lis_result_sourcedid(cls, context, request):
        """Create or update a record of LIS result/outcome data for a student launch."""

        if (
            request.lti_user.is_instructor
            or request.params.get("tool_consumer_info_product_family_code") == "canvas"
        ):
            return

        try:
            lis_result_sourcedid = LISResultSourcedIdSchema(
                request
            ).lis_result_sourcedid_info()
        except ValidationError:
            # We're missing something we need in the request.
            # This can happen if the user is not a student, or if the needed
            # LIS data is not present on the request.
            return

        lis_result_svc = request.find_service(name="lis_result_sourcedid")
        lis_result_svc.upsert(
            lis_result_sourcedid, h_user=context.h_user, lti_user=request.lti_user
        )
