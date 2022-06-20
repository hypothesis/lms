"""
Views for handling what the LTI spec calls "Basic LTI Launches".

A Basic LTI Launch is the form submission POST request that an LMS sends us
when it wants our app to launch an assignment, as opposed to other kinds of
LTI launches such as the deep linking launches that some LMS's
send us while *creating* a new assignment.

The spec requires Basic LTI Launch requests to have an ``lti_message_type``
parameter with the value ``basic-lti-launch-request`` to distinguish them
from other types of launch request (other "message types") but our code
doesn't actually require basic launch requests to have this parameter.
"""

from pyramid.view import view_config, view_defaults

from lms.models import LtiLaunches
from lms.security import Permissions
from lms.services import DocumentURLService, LTIRoleService
from lms.services.assignment import AssignmentService
from lms.validation import BasicLTILaunchSchema, ConfigureAssignmentSchema
from lms.validation.authentication import BearerTokenSchema


def has_document_url(context, request):
    """Get if the current launch has a resolvable document URL."""
    return bool(
        request.find_service(DocumentURLService).get_document_url(context, request)
    )


def is_authorized_to_configure_assignments(_context, request):
    """Get if the current user allowed to configured assignments."""

    if not request.lti_user:
        return False

    roles = request.lti_user.roles.lower()

    return any(
        role in roles for role in ["administrator", "instructor", "teachingassistant"]
    )


# This is imported in `lms.views.predicates`
LTI_LAUNCH_PREDICATES = {
    "has_document_url": has_document_url,
    "authorized_to_configure_assignments": is_authorized_to_configure_assignments,
}


@view_defaults(
    permission=Permissions.LTI_LAUNCH_ASSIGNMENT,
    renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    request_method="POST",
    route_name="lti_launches",
    schema=BasicLTILaunchSchema,
)
class BasicLaunchViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.assignment_service: AssignmentService = request.find_service(
            name="assignment"
        )

        self.application_instance = request.find_service(
            name="application_instance"
        ).get_current()
        self.application_instance.check_guid_aligns(
            self.context.lti_params.get("tool_consumer_instance_guid")
        )

        self._record_launch()

    @view_config(has_document_url=True)
    def configured_launch(self):
        """
        Respond to a configured assignment launch.

        This is any launch where the document URL service can resolve the
        correct document to show.
        """

        return self._show_document(
            document_url=self.request.find_service(DocumentURLService).get_document_url(
                self.context, self.request
            )
        )

    @view_config(
        has_document_url=False,
        authorized_to_configure_assignments=True,
        renderer="lms:templates/file_picker.html.jinja2",
    )
    def unconfigured_launch(self):
        """
        Respond to an unconfigured assignment launch.

        Unconfigured assignment launch requests don't contain any document URL
        or file ID because the assignment's document hasn't been chosen yet.
        This happens in LMS's that don't support LTI deep linking.
        They go straight from assignment creation to launching the assignment
        without the user having had a chance to choose a document.

        When this happens we show the user our document-selection form instead
        of launching the assignment. The user will choose the document and
        we'll save it in our DB. Subsequent launches of the same assignment
        will then be DB-configured launches rather than unconfigured.
        """
        form_fields = {
            param: value
            for param, value in self.context.lti_params.items()
            # Don't send over auth related params. We'll use our own authorization header
            if param
            not in ["oauth_nonce", "oauth_timestamp", "oauth_signature", "id_token"]
        }

        form_fields["authorization"] = BearerTokenSchema(
            self.request
        ).authorization_param(self.request.lti_user)

        self.context.js_config.enable_file_picker_mode(
            form_action=self.request.route_url("configure_assignment"),
            form_fields=form_fields,
        )

        return {}

    @view_config(
        has_document_url=False,
        authorized_to_configure_assignments=False,
        renderer="lms:templates/lti/basic_launch/unconfigured_launch_not_authorized.html.jinja2",
    )
    def unconfigured_launch_not_authorized(self):
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
        route_name="configure_assignment",
        schema=ConfigureAssignmentSchema,
    )
    def configure_assignment(self):
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
        extra = {}
        if group_set := self.request.parsed_params.get("group_set"):
            extra["group_set_id"] = group_set

        return self._show_document(
            document_url=self.request.parsed_params["document_url"],
            assignment_extra=extra,
        )

    def _show_document(self, document_url, assignment_extra=None):
        """
        Display a document to the user for annotation or grading.

        :param document_url: URL of the document to display
        :param assignment_extra: Any extra details to add to the assignment
            when updating metadata.
        """

        # Before any LTI assignments launch, create or update the Hypothesis
        # user and group corresponding to the LTI user and course.
        self.request.find_service(name="lti_h").sync(
            [self.context.course], self.context.lti_params
        )

        # An assignment has been configured in the LMS as "gradable" if it has
        # the `lis_outcome_service_url` param
        assignment_gradable = bool(
            self.context.lti_params.get("lis_outcome_service_url")
        )

        # Store lots of info about the assignment
        self._record_assignment(
            document_url, extra=assignment_extra, is_gradable=assignment_gradable
        )

        # Set up the JS config for the front-end
        self._configure_js_to_show_document(document_url, assignment_gradable)

        return {}

    def _record_assignment(self, document_url, extra, is_gradable):
        # Store assignment details
        assignment = self.assignment_service.upsert_assignment(
            document_url=document_url,
            tool_consumer_instance_guid=self.context.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=self.context.resource_link_id,
            lti_params=self.context.lti_params,
            extra=extra,
            is_gradable=is_gradable,
        )

        # Store the relationship between the assignment and the course
        self.assignment_service.upsert_assignment_membership(
            assignment=assignment,
            user=self.request.user,
            lti_roles=self.request.find_service(LTIRoleService).get_roles(
                self.context.lti_params["roles"]
            ),
        )
        # Store the relationship between the assignment and the course
        self.assignment_service.upsert_assignment_groupings(
            assignment=assignment, groupings=[self.context.course]
        )

    def _configure_js_to_show_document(self, document_url, assignment_gradable):
        if self.context.is_canvas:
            # For students in Canvas with grades to submit we need to enable
            # Speedgrader settings for gradable assignments
            # `lis_result_sourcedid` associates a specific user with an
            # assignment.
            if (
                assignment_gradable
                and self.request.lti_user.is_learner
                and self.context.lti_params.get("lis_result_sourcedid")
            ):
                self.context.js_config.add_canvas_speedgrader_settings(document_url)

            # We add a `focused_user` query param to the SpeedGrader LTI launch
            # URLs we submit to Canvas for each student when the student
            # launches an assignment. Later, Canvas uses these URLs to launch
            # us when a teacher grades the assignment in SpeedGrader.
            if focused_user := self.request.params.get("focused_user"):
                self.context.js_config.set_focused_user(focused_user)

        elif assignment_gradable and self.request.lti_user.is_instructor:
            # Only show the grading interface to teachers who aren't in Canvas,
            # as Canvas uses its own built in Speedgrader

            self.context.js_config.enable_grading_bar()

        self.context.js_config.add_document_url(document_url)
        self.context.js_config.enable_lti_launch_mode()

    def _record_launch(self):
        """Persist launch type independent info to the DB."""

        self.application_instance.update_lms_data(self.context.lti_params)

        # Record all LTILaunches for future reporting
        LtiLaunches.add(
            self.request.db,
            self.context.lti_params.get("context_id"),
            self.context.lti_params.get("oauth_consumer_key"),
        )

        if not self.request.lti_user.is_instructor and not self.context.is_canvas:
            # Create or update a record of LIS result data for a student launch
            self.request.find_service(name="grading_info").upsert_from_request(
                self.request
            )
