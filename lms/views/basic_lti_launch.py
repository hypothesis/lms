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
from lms.validation import (
    BasicLTILaunchSchema,
    ConfigureModuleItemSchema,
    URLConfiguredBasicLTILaunchSchema,
)
from lms.validation.authentication import BearerTokenSchema


@view_defaults(
    permission="launch_lti_assignment",
    renderer="lms:templates/basic_lti_launch/basic_lti_launch.html.jinja2",
    request_method="POST",
    route_name="lti_launches",
    schema=BasicLTILaunchSchema,
)
class BasicLTILaunchViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.course_service = request.find_service(name="course")

        self.context.js_config.enable_lti_launch_mode()
        self.context.js_config.maybe_set_focused_user()

    def sync_lti_data_to_h(self):
        """
        Sync LTI data to H.

        Before any LTI assignment launch create or update the Hypothesis user
        and group corresponding to the LTI user and course.
        """

        self.request.find_service(name="lti_h").sync(
            [self.context.h_group], self.request.params,
        )

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

        if not lti_user.is_instructor and not self.context.is_canvas:
            # Create or update a record of LIS result data for a student launch
            request.find_service(name="grading_info").upsert_from_request(
                request, h_user=lti_user.h_user, lti_user=lti_user
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
        self.course_service.get_or_create(self.context.h_group.authority_provided_id)
        self.context.js_config.add_canvas_file_id(self.request.params["file_id"])
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
        self.course_service.get_or_create(self.context.h_group.authority_provided_id)

        self.context.js_config.maybe_enable_grading()

        resource_link_id = self.request.params["resource_link_id"]
        tool_consumer_instance_guid = self.request.params["tool_consumer_instance_guid"]

        # The ``db_configured=True`` view predicate ensures that this view
        # won't be called if there isn't a matching ModuleItemConfiguration in
        # the DB. So here we can safely assume that the ModuleItemConfiguration
        # exists.
        document_url = ModuleItemConfiguration.get_document_url(
            self.request.db, tool_consumer_instance_guid, resource_link_id
        )

        self.context.js_config.add_document_url(document_url)

        return {}

    @view_config(url_configured=True, schema=URLConfiguredBasicLTILaunchSchema)
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
        self.course_service.get_or_create(self.context.h_group.authority_provided_id)
        self.context.js_config.maybe_enable_grading()
        self.context.js_config.add_document_url(self.request.parsed_params["url"])
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
        self.course_service.get_or_create(self.context.h_group.authority_provided_id)

        form_fields = {
            param: value
            for param, value in self.request.params.items()
            if param not in ["oauth_nonce", "oauth_timestamp", "oauth_signature"]
        }

        form_fields["authorization"] = BearerTokenSchema(
            self.request
        ).authorization_param(self.request.lti_user)

        self.context.js_config.enable_content_item_selection_mode(
            form_action=self.request.route_url("module_item_configurations"),
            form_fields=form_fields,
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

        self.context.js_config.add_document_url(document_url)

        self.sync_lti_data_to_h()
        self.store_lti_data()

        self.context.js_config.maybe_enable_grading()

        return {}
