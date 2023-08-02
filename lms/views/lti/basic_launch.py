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

from lms.events import LTIEvent
from lms.product.plugin.grading import GradingPlugin
from lms.security import Permissions
from lms.services.assignment import AssignmentService
from lms.validation import BasicLTILaunchSchema, ConfigureAssignmentSchema


@view_defaults(
    request_method="POST",
    permission=Permissions.LTI_LAUNCH_ASSIGNMENT,
    schema=BasicLTILaunchSchema,
)
class BasicLaunchViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self._grading_plugin: GradingPlugin = request.product.plugin.grading
        self.assignment_service: AssignmentService = request.find_service(
            name="assignment"
        )
        self._guid = self.request.lti_params.get("tool_consumer_instance_guid")
        self._resource_link_id = self.request.lti_params.get("resource_link_id")

        self.request.lti_user.application_instance.check_guid_aligns(self._guid)
        self.request.find_service(name="application_instance").update_from_lti_params(
            self.request.lti_user.application_instance, self.request.lti_params
        )
        self.course = self._record_course()

    @view_config(
        route_name="lti_launches",
        renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    )
    def lti_launch(self):
        """Handle regular LTI launches."""

        if assignment := self.assignment_service.get_assignment_for_launch(
            self.request
        ):
            self.request.override_renderer = (
                "lms:templates/lti/basic_launch/basic_launch.html.jinja2"
            )
            self._show_document(assignment)
            self.request.registry.notify(
                LTIEvent(request=self.request, type=LTIEvent.Type.CONFIGURED_LAUNCH)
            )
            return {}

        # Show the file-picker for the user to choose a document.
        # This happens if we cannot resolve a document URL for any reason.
        self.request.override_renderer = "lms:templates/file_picker.html.jinja2"
        self._configure_js_for_file_picker()

        return {}

    @view_config(route_name="lti.reconfigure", renderer="json")
    def reconfigure_assignment_config(self):
        """Return the data needed to re-configure an assignment."""
        assignment = self.assignment_service.get_assignment(
            tool_consumer_instance_guid=self._guid,
            resource_link_id=self._resource_link_id,
        )
        config = self._configure_js_for_file_picker(route="edit_assignment")
        return {
            # Info about the assignment's current configuration
            "assignment": {
                "group_set_id": assignment.extra.get("group_set_id"),
                "document": {
                    "url": assignment.document_url,
                },
            },
            # Data needed to re-configure it
            "filePicker": config["filePicker"],
        }

    @view_config(
        route_name="configure_assignment",
        permission=Permissions.LTI_CONFIGURE_ASSIGNMENT,
        schema=ConfigureAssignmentSchema,
        renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    )
    def configure_assignment_callback(self):
        """
        Save the configuration from the file-picker for future launches.

        We then continue as if we were already configured with this document
        and display it to the user.
        """
        assignment = self.assignment_service.create_assignment(
            tool_consumer_instance_guid=self._guid,
            resource_link_id=self._resource_link_id,
        )

        self._configure_assignment(assignment)
        return self._show_document(assignment)

    @view_config(
        route_name="edit_assignment",
        permission=Permissions.LTI_CONFIGURE_ASSIGNMENT,
        schema=ConfigureAssignmentSchema,
        renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    )
    def edit_assignment_callback(self):
        """Edit the configuration of an existing assignment."""
        assignment = self.assignment_service.get_assignment(
            tool_consumer_instance_guid=self._guid,
            resource_link_id=self._resource_link_id,
        )
        self.request.registry.notify(
            LTIEvent(
                request=self.request,
                type=LTIEvent.Type.EDITED_ASSIGNMENT,
                data={
                    "old_url": assignment.document_url,
                    "old_group_set_id": assignment.extra.get("group_set_id"),
                },
            )
        )
        self._configure_assignment(assignment)
        return self._show_document(assignment)

    def _show_document(self, assignment):
        """Display a document to the user for annotation or grading."""

        # Before any LTI assignments launch, create or update the Hypothesis
        # user and group corresponding to the LTI user and course.
        self.request.find_service(name="lti_h").sync(
            [self.course], self.request.lti_params
        )

        # Store the relationship between the assignment and the course
        self.assignment_service.upsert_assignment_membership(
            assignment=assignment,
            user=self.request.user,
            lti_roles=self.request.lti_user.lti_roles,
        )
        # Store the relationship between the assignment and the course
        self.assignment_service.upsert_assignment_groupings(
            assignment, groupings=[self.course]
        )

        # Set up grading
        self._grading_plugin.configure_grading_for_launch(
            self.request, self.context.js_config, assignment
        )

        # Set up the JS config for the front-end
        self.context.js_config.add_document_url(assignment.document_url)
        self.context.js_config.enable_lti_launch_mode(self.course, assignment)

        return {}

    def _record_course(self):
        course = self.request.find_service(name="course").get_from_launch(
            self.request.product, self.request.lti_params
        )
        self.request.find_service(name="grouping").upsert_grouping_memberships(
            user=self.request.user, groups=[course]
        )
        return course

    def _configure_assignment(self, assignment):
        """
        Prepare an assignment with new configuration.

        The configuration could be because we are creating this assignment
        for the first time or from an edit.
        """
        self.assignment_service.update_assignment(
            self.request,
            assignment,
            document_url=self.request.parsed_params["document_url"],
            group_set_id=self.request.parsed_params.get("group_set"),
        )

    def _configure_js_for_file_picker(
        self, route: str = "configure_assignment"
    ) -> dict:
        """
        Show the file-picker for the user to choose a document.

        We'll use this mode to configure new assignments and to reconfigure existing ones.
        """

        if not self.request.has_permission(Permissions.LTI_CONFIGURE_ASSIGNMENT):
            # Looks like the user is not an instructor, so show an error page

            # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr
            # /renderers.html?highlight=override_renderer#overriding-a-renderer-at-runtime
            self.request.override_renderer = "lms:templates/lti/basic_launch/unconfigured_launch_not_authorized.html.jinja2"
            return {}

        return self.context.js_config.enable_file_picker_mode(
            form_action=self.request.route_url(route),
            form_fields=self.request.lti_params.serialize(
                authorization=self.context.js_config.auth_token
            ),
        )
