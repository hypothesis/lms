from pyramid.view import view_config

from lms.models import Grouping
from lms.security import Permissions
from lms.services import UserService
from lms.validation import APIBlackboardSyncSchema
from lms.views.api.exceptions import GroupError


class BlackboardStudentNotInGroup(GroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "blackboard_student_not_in_group"


class BlackboardGroupSetEmpty(GroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "blackboard_group_set_empty"


class Sync:
    def __init__(self, request):
        self.request = request
        self.grouping_service = self.request.find_service(name="grouping")
        self.blackboard_api = self.request.find_service(name="blackboard_api_client")

        self.tool_consumer_instance_guid = self.request.parsed_params["lms"][
            "tool_consumer_instance_guid"
        ]

    @view_config(
        route_name="blackboard_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
        schema=APIBlackboardSyncSchema,
    )
    def sync(self):
        groups = self.get_blackboard_groups()

        self.sync_to_h(groups)

        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    def get_blackboard_groups(self):
        lti_user = self.request.lti_user
        group_set_id = self.group_set()
        course_id = self.request.parsed_params["course"]["context_id"]
        course = self.get_course(course_id)

        if lti_user.is_learner:
            user = self.request.find_service(UserService).get(
                self.request.find_service(name="application_instance").get_current(),
                lti_user.user_id,
            )

            learner_groups = self.blackboard_api.course_groups(
                course_id, group_set_id, current_student_own_groups_only=True
            )
            if not learner_groups:
                raise BlackboardStudentNotInGroup(group_set=group_set_id)

            groups = self.to_groups_groupings(course, learner_groups)
            self.grouping_service.upsert_grouping_memberships(user, groups)
            return groups

        if grading_student_id := self.request.parsed_params.get("gradingStudentId"):
            return self.grouping_service.get_course_groupings_for_user(
                course,
                grading_student_id,
                type_=Grouping.Type.BLACKBOARD_GROUP,
                group_set_id=group_set_id,
            )

        groups = self.blackboard_api.group_set_groups(course_id, group_set_id)
        if not groups:
            raise BlackboardGroupSetEmpty(group_set=group_set_id)

        return self.to_groups_groupings(course, groups)

    def group_set(self):
        return (
            self.request.find_service(name="assignment")
            .get(
                self.tool_consumer_instance_guid,
                self.request.parsed_params["assignment"]["resource_link_id"],
            )
            .extra["group_set_id"]
        )

    def to_groups_groupings(self, course, groups):
        return [
            self.grouping_service.upsert_with_parent(
                tool_consumer_instance_guid=self.tool_consumer_instance_guid,
                lms_id=group["id"],
                lms_name=group["name"],
                parent=course,
                type_=Grouping.Type.BLACKBOARD_GROUP,
                extra={"group_set_id": group["groupSetId"]},
            )
            for group in groups
        ]

    def sync_to_h(self, groups):
        lti_h_svc = self.request.find_service(name="lti_h")
        group_info = self.request.parsed_params["group_info"]
        lti_h_svc.sync(groups, group_info)

    def get_course(self, course_id):
        course_service = self.request.find_service(name="course")
        return course_service.get(
            course_service.generate_authority_provided_id(
                self.tool_consumer_instance_guid, course_id
            )
        )
