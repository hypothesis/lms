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

from lms.events.event import LTIEvent
from lms.security import Permissions
from lms.services import DocumentURLService, LTILaunchService
from lms.validation import BasicLTILaunchSchema, ConfigureAssignmentSchema
from lms.validation.authentication import BearerTokenSchema


def has_document_url(_context, request):
    """
    Get if the current launch has a resolvable document URL.

    This is imported into `lms.views.predicates` to provide the
    `has_document_url` predicate.
    """
    return bool(request.find_service(DocumentURLService).get_document_url(request))


@view_defaults(
    request_method="POST",
    permission=Permissions.LTI_LAUNCH_ASSIGNMENT,
    schema=BasicLTILaunchSchema,
)
class BasicLaunchViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.lti_launch_service: LTILaunchService = request.find_service(
            LTILaunchService
        )

        self.lti_launch_service.validate_launch()
        self.lti_launch_service.record_launch(request)

    @view_config(
        route_name="lti_launches",
        has_document_url=True,
        renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    )
    def configured_launch(self):
        """Display a document if we can resolve one to show."""

        self._show_document(
            document_url=self.request.find_service(DocumentURLService).get_document_url(
                self.request
            )
        )
        self.request.registry.notify(
            LTIEvent(request=self.request, type=LTIEvent.Type.CONFIGURED_LAUNCH)
        )
        return {}

    @view_config(
        route_name="lti_launches",
        has_document_url=False,
        renderer="lms:templates/file_picker.html.jinja2",
    )
    def unconfigured_launch(self):
        """
        Show the file-picker for the user to choose a document.

        This happens if we cannot resolve a document URL for any reason.
        """

        if not self.request.has_permission(Permissions.LTI_CONFIGURE_ASSIGNMENT):
            # Looks like the user is not an instructor, so show an error page

            # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr
            # /renderers.html?highlight=override_renderer#overriding-a-renderer-at-runtime
            self.request.override_renderer = "lms:templates/lti/basic_launch/unconfigured_launch_not_authorized.html.jinja2"
            return {}

        form_fields = {
            param: value
            for param, value in self.request.lti_params.items()
            # Don't send over auth related params. We'll use our own
            # authorization header
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
        route_name="configure_assignment",
        permission=Permissions.LTI_CONFIGURE_ASSIGNMENT,
        schema=ConfigureAssignmentSchema,
        renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    )
    def configure_assignment(self):
        """
        Save the configuration from the file-picker for future launches.

        We then continue as if we were already configured with this document
        and display it to the user.
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

        course = self.lti_launch_service.record_course()
        assignment = self.lti_launch_service.record_assignment(
            course, document_url, extra=assignment_extra
        )

        # Before any LTI assignments launch, create or update the Hypothesis
        # user and group corresponding to the LTI user and course.
        self.request.find_service(name="lti_h").sync([course], self.request.lti_params)

        # Set up the JS config for the front-end
        self._configure_js_to_show_document(document_url, assignment)

        return {}

    def _configure_js_to_show_document(self, document_url, assignment):
        if self.context.is_canvas:
            # For students in Canvas with grades to submit we need to enable
            # Speedgrader settings for gradable assignments
            # `lis_result_sourcedid` associates a specific user with an
            # assignment.
            if (
                assignment.is_gradable
                and self.request.lti_user.is_learner
                and self.request.lti_params.get("lis_result_sourcedid")
            ):
                self.context.js_config.add_canvas_speedgrader_settings(document_url)

            # We add a `focused_user` query param to the SpeedGrader LTI launch
            # URLs we submit to Canvas for each student when the student
            # launches an assignment. Later, Canvas uses these URLs to launch
            # us when a teacher grades the assignment in SpeedGrader.
            if focused_user := self.request.params.get("focused_user"):
                self.context.js_config.set_focused_user(focused_user)

        elif assignment.is_gradable and self.request.lti_user.is_instructor:
            # Only show the grading interface to teachers who aren't in Canvas,
            # as Canvas uses its own built in Speedgrader

            self.context.js_config.enable_grading_bar()

        self.context.js_config.add_document_url(document_url)
        self.context.js_config.enable_lti_launch_mode(assignment)
