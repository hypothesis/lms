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
from lms.product import Product
from lms.security import Permissions
from lms.services import DocumentURLService, LTIRoleService
from lms.services.assignment import AssignmentService
from lms.services.grouping import GroupingService
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
        self.plugin = self.request.product.plugin.lti_launch
        self.assignment_service: AssignmentService = request.find_service(
            name="assignment"
        )
        self.grouping_service: GroupingService = request.find_service(name="grouping")

        self.context.application_instance.check_guid_aligns(
            self.request.lti_params.get("tool_consumer_instance_guid")
        )

        self._record_launch()

    @view_config(
        route_name="lti_launches",
        has_document_url=True,
        renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    )
    def configured_launch(self):
        """Display a document if we can resolve one to show."""

        return self._show_document(
            document_url=self.request.find_service(DocumentURLService).get_document_url(
                self.request
            )
        )

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

        # Before any LTI assignments launch, create or update the Hypothesis
        # user and group corresponding to the LTI user and course.
        self.request.find_service(name="lti_h").sync(
            [self.context.course], self.request.lti_params
        )

        # An assignment has been configured in the LMS as "gradable" if it has
        # the `lis_outcome_service_url` param
        assignment_gradable = bool(
            self.request.lti_params.get("lis_outcome_service_url")
        )

        # Store lots of info
        self._record_course()
        assignment = self._record_assignment(
            document_url, extra=assignment_extra, is_gradable=assignment_gradable
        )

        # Set up the JS config for the front-end
        self._configure_js_to_show_document(
            document_url, assignment, assignment_gradable
        )

        return {}

    def _record_assignment(self, document_url, extra, is_gradable):
        # Store assignment details
        assignment = self.assignment_service.upsert_assignment(
            document_url=document_url,
            tool_consumer_instance_guid=self.request.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=self.request.lti_params.get("resource_link_id"),
            lti_params=self.request.lti_params,
            extra=extra,
            is_gradable=is_gradable,
        )

        # Store the relationship between the assignment and the course
        self.assignment_service.upsert_assignment_membership(
            assignment=assignment,
            user=self.request.user,
            lti_roles=self.request.find_service(LTIRoleService).get_roles(
                self.request.lti_params["roles"]
            ),
        )
        # Store the relationship between the assignment and the course
        self.assignment_service.upsert_assignment_groupings(
            assignment=assignment, groupings=[self.context.course]
        )

        return assignment

    def _record_course(self):
        # It's not completely clear but accessing a course in this way actually
        # is an upsert. So this stores the course as well
        self.grouping_service.upsert_grouping_memberships(
            user=self.request.user, groups=[self.context.course]
        )

    def _configure_js_to_show_document(
        self, document_url, assignment, assignment_gradable
    ):
        self.plugin.add_to_launch_js_config(self.context.js_config)

        if (
            self.plugin.supports_grading_bar
            and assignment_gradable
            and self.request.lti_user.is_instructor
        ):
            # Only show the grading interface to teachers who aren't in Canvas,
            # as Canvas uses its own built in Speedgrader

            self.context.js_config.enable_grading_bar()

        self.context.js_config.add_document_url(document_url)
        self.context.js_config.enable_lti_launch_mode(assignment)

    def _record_launch(self):
        """Persist launch type independent info to the DB."""

        self.context.application_instance.update_lms_data(self.request.lti_params)

        # Record all LTILaunches for future reporting
        LtiLaunches.add(
            self.request.db,
            self.request.lti_params.get("context_id"),
            self.request.lti_params.get("oauth_consumer_key"),
        )

        if self.plugin.supports_grading_bar and not self.request.lti_user.is_instructor:
            # Create or update a record of LIS result data for a student launch
            self.request.find_service(name="grading_info").upsert_from_request(
                self.request
            )
