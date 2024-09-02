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

import logging

from pyramid.view import view_config, view_defaults

from lms.events import LTIEvent
from lms.models import Assignment
from lms.product.plugin.misc import MiscPlugin
from lms.security import Permissions
from lms.services import LTIGradingService, VitalSourceService
from lms.services.assignment import AssignmentService
from lms.validation import BasicLTILaunchSchema, ConfigureAssignmentSchema

LOG = logging.getLogger(__name__)


@view_defaults(
    request_method="POST",
    permission=Permissions.LTI_LAUNCH_ASSIGNMENT,
    schema=BasicLTILaunchSchema,
)
class BasicLaunchViews:
    def __init__(self, context, request) -> None:
        self.context = context
        self.request = request

        self._misc_plugin: MiscPlugin = request.product.plugin.misc
        self.assignment_service: AssignmentService = request.find_service(
            name="assignment"
        )
        self._course_service = self.request.find_service(name="course")
        self._guid = self.request.lti_params.get("tool_consumer_instance_guid")
        self._resource_link_id = self.request.lti_params.get("resource_link_id")

        self.request.lti_user.application_instance.check_guid_aligns(self._guid)

        # This might raise ReausedCondumerKey, preventing the launch
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

        assignment = self.assignment_service.get_assignment_for_launch(
            self.request, self.course
        )

        if error_code := self.request.find_service(VitalSourceService).check_h_license(
            self.request.lti_user, self.request.lti_params, assignment
        ):
            self.request.override_renderer = "lms:templates/error_dialog.html.jinja2"
            self.context.js_config.enable_error_dialog_mode(error_code)
            return {}

        if assignment:
            self.request.override_renderer = (
                "lms:templates/lti/basic_launch/basic_launch.html.jinja2"
            )
            self._show_document(assignment)
            self.request.registry.notify(
                LTIEvent.from_request(
                    request=self.request, type_=LTIEvent.Type.CONFIGURED_LAUNCH
                )
            )
            return {}

        # Show the file-picker for the user to choose a document.
        # This happens if we cannot resolve a document URL for any reason.
        self.request.override_renderer = "lms:templates/file_picker.html.jinja2"
        self._configure_js_for_file_picker(assignment)

        return {}

    @view_config(route_name="lti.reconfigure", renderer="json")
    def reconfigure_assignment_config(self):
        """Return the data needed to re-configure an assignment."""
        assignment = self.assignment_service.get_assignment(
            tool_consumer_instance_guid=self._guid,
            resource_link_id=self._resource_link_id,
        )
        config = self._configure_js_for_file_picker(assignment, route="edit_assignment")
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
            LTIEvent.from_request(
                request=self.request,
                type_=LTIEvent.Type.EDITED_ASSIGNMENT,
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

        # Store the relationship between the assignment and the user
        self.assignment_service.upsert_assignment_membership(
            assignment=assignment,
            user=self.request.user,
            lti_roles=self.request.lti_user.lti_roles,
        )
        # Store the relationship between the assignment and the course
        self.assignment_service.upsert_assignment_groupings(
            assignment, groupings=[self.course]
        )

        if (
            self.request.product.use_toolbar_editing
            and self.request.lti_user.is_instructor
        ):
            self.context.js_config.enable_toolbar_editing()

        if self.request.product.use_toolbar_grading and assignment.is_gradable:
            if self.request.lti_user.is_instructor:
                # Get the list of students to display in the drop down
                students = self.request.find_service(
                    name="grading_info"
                ).get_students_for_grading(
                    application_instance=self.request.lti_user.application_instance,
                    context_id=self.request.lti_params.get("context_id"),
                    resource_link_id=self.request.lti_params.get("resource_link_id"),
                    lis_outcome_service_url=self.request.lti_params[
                        "lis_outcome_service_url"
                    ],
                )

                # Refresh the max score for this assignment
                score_maximum = self.request.find_service(
                    LTIGradingService
                ).get_score_maximum(assignment.resource_link_id)
                LOG.debug(
                    "Score maximum for %s: %s",
                    assignment.resource_link_id,
                    score_maximum,
                )

                # Display the grading interface in the toolbar
                self.context.js_config.enable_toolbar_grading(
                    students=students, score_maximum=score_maximum
                )

            if not self.request.lti_user.is_instructor:
                # Create or update a record of LIS result data for a student launch
                # We'll query these rows to populate the student drop down in the
                # instructor toolbar
                self.request.find_service(name="grading_info").upsert(
                    self.request.lti_user,
                    self.request.lti_params.get("lis_result_sourcedid"),
                    self.request.lti_params.get("lis_outcome_service_url"),
                )

        # Set up the JS config for the front-end
        self.context.js_config.add_document_url(assignment.document_url)
        self.context.js_config.enable_lti_launch_mode(self.course, assignment)

        if self.request.lti_user.is_instructor:
            self.context.js_config.enable_instructor_dashboard_entry_point(assignment)

        # If there are any Hypothesis client feature flags that need to be
        # enabled based on the current application instance settings, those
        # should be enabled here via `self.context.js_config.enable_client_feature`.
        #
        # There are currently no such features.

        # Run any non standard code for the current product
        self._misc_plugin.post_launch_assignment_hook(
            self.request, self.context.js_config, assignment
        )

        return {}

    def _record_course(self):
        course = self._course_service.get_from_launch(
            self.request.product.family, self.request.lti_params
        )
        self.request.find_service(name="grouping").upsert_grouping_memberships(
            user=self.request.user, groups=[course]
        )
        self._course_service.upsert_lms_course_membership(
            lms_course=course.lms_course,
            lms_user=self.request.user.lms_user,
            lti_roles=self.request.lti_user.lti_roles,
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
            course=self.course,
            auto_grading_config=None,
        )

    def _configure_js_for_file_picker(
        self, assignment: Assignment | None, route: str = "configure_assignment"
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
            course=self.course,
            assignment=assignment,
        )
