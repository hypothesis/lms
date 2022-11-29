from lms.models import ApplicationInstance, LTIParams, LTIUser, User
from lms.services.application_instance import ApplicationInstanceService
from lms.services.assignment import AssignmentService
from lms.services.grading_info import GradingInfoService
from lms.services.grouping import GroupingService
from lms.services.lti_role_service import LTIRoleService


class LTILaunchService:
    # pylint:disable=too-many-instance-attributes,too-many-arguments
    def __init__(
        self,
        lti_params: LTIParams,
        user: User,
        lti_user: LTIUser,
        course_service,
        assignment_service: AssignmentService,
        grouping_service: GroupingService,
        lti_role_service: LTIRoleService,
        application_instance_service: ApplicationInstanceService,
        grading_info_service: GradingInfoService,
        product,
        plugin,
    ):
        self._lti_params = lti_params
        self._user = user
        self._application_instance: ApplicationInstance = user.application_instance
        self.lti_user = lti_user
        self._grouping_service = grouping_service
        self._course_service = course_service
        self._assignment_service = assignment_service
        self._lti_role_service = lti_role_service
        self._application_instance_service = application_instance_service
        self._grading_info_service = grading_info_service
        self._product = product
        self._plugin = plugin

    def validate_launch(self):
        self._application_instance.check_guid_aligns(
            self._lti_params.get("tool_consumer_instance_guid")
        )

    def record_course(self):
        """Insert or update the course for the current launch."""
        course = self._course_service.upsert_course(
            context_id=self._lti_params["context_id"],
            name=self._lti_params["context_title"],
            extra=self._plugin.course_extra(self._lti_params),
        )
        self._grouping_service.upsert_grouping_memberships(
            user=self._user, groups=[course]
        )
        return course

    def record_assignment(self, course, document_url, extra):
        """Store assignment details."""
        assignment = self._assignment_service.upsert_assignment(
            document_url=document_url,
            tool_consumer_instance_guid=self._lti_params["tool_consumer_instance_guid"],
            resource_link_id=self._lti_params.get("resource_link_id"),
            lti_params=self._lti_params,
            extra=extra,
            is_gradable=self._plugin.is_assignment_gradable(self._lti_params),
        )

        # Store the relationship between the assignment and the course
        self._assignment_service.upsert_assignment_membership(
            assignment=assignment,
            user=self._user,
            lti_roles=self._lti_role_service.get_roles(self._lti_params["roles"]),
        )
        # Store the relationship between the assignment and the course
        self._assignment_service.upsert_assignment_groupings(
            assignment_id=assignment.id, groupings=[course]
        )

        return assignment

    def record_launch(self, request):
        """Persist launch type independent info to the DB."""
        self._application_instance_service.update_from_lti_params(
            self._application_instance, self._lti_params
        )

        if self._product.use_grading_bar and not self.lti_user.is_instructor:
            # Create or update a record of LIS result data for a student launch
            self._grading_info_service.upsert_from_request(request)


def factory(_context, request):
    return LTILaunchService(
        lti_params=request.lti_params,
        user=request.user,
        lti_user=request.lti_user,
        course_service=request.find_service(name="course"),
        assignment_service=request.find_service(name="assignment"),
        grouping_service=request.find_service(name="grouping"),
        lti_role_service=request.find_service(LTIRoleService),
        application_instance_service=request.find_service(name="application_instance"),
        grading_info_service=request.find_service(name="grading_info"),
        product=request.product,
        plugin=request.product.plugin.launch,
    )
