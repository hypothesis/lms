from pyramid.view import view_config

from lms.models import Grouping
from lms.security import Permissions
from lms.services import UserService
from lms.services.exceptions import ExternalRequestError
from lms.validation import APIBlackboardSyncSchema
from lms.views.api.exceptions import GroupError


class BlackboardStudentNotInGroup(GroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "blackboard_student_not_in_group"


class BlackboardGroupSetEmpty(GroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "blackboard_group_set_empty"


class BlackboardGroupSetNotFound(GroupError):
    error_code = "blackboard_group_set_not_found"


class Sync:
    def __init__(self, request):
        self.request = request
        self.grouping_service = self.request.find_service(name="grouping")
        self.blackboard_api = self.request.find_service(name="blackboard_api_client")

    @view_config(
        route_name="blackboard_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
        schema=APIBlackboardSyncSchema,
    )
    def sync(self):
        params = self.request.parsed_params
        tool_consumer_instance_guid = params["lms"]["tool_consumer_instance_guid"]
        course = self.get_course(
            params["course"]["context_id"], tool_consumer_instance_guid
        )
        group_set_id = self.group_set(
            tool_consumer_instance_guid, params["assignment"]["resource_link_id"]
        )

        groups = self.get_blackboard_groups(
            course, group_set_id, params.get("gradingStudentId")
        )
        self.request.find_service(name="lti_h").sync(groups, params["group_info"])
        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    def get_blackboard_groups(self, course, group_set_id, grading_student_id=None):
        lti_user = self.request.lti_user

        if lti_user.is_learner:
            user = self.request.find_service(UserService).get(
                course.application_instance,
                lti_user.user_id,
            )

            learner_groups = self.blackboard_api.course_groups(
                course.lms_id, group_set_id, current_student_own_groups_only=True
            )
            if not learner_groups:
                raise BlackboardStudentNotInGroup(group_set=group_set_id)

            groups = self.to_groups_groupings(course, learner_groups)
            self.grouping_service.upsert_grouping_memberships(user, groups)
            return groups

        if grading_student_id:
            return self.grouping_service.get_course_groupings_for_user(
                course,
                grading_student_id,
                type_=Grouping.Type.BLACKBOARD_GROUP,
                group_set_id=group_set_id,
            )

        try:
            groups = self.blackboard_api.group_set_groups(course.lms_id, group_set_id)
        except ExternalRequestError as bb_api_error:
            if bb_api_error.status_code == 404:
                raise BlackboardGroupSetNotFound(
                    group_set=group_set_id
                ) from bb_api_error

            raise bb_api_error

        if not groups:
            raise BlackboardGroupSetEmpty(group_set=group_set_id)

        return self.to_groups_groupings(course, groups)

    def to_groups_groupings(self, course, groups):
        return self.grouping_service.upsert_with_parent(
            [
                {
                    "lms_id": group["id"],
                    "lms_name": group["name"],
                    "extra": {"group_set_id": group["groupSetId"]},
                }
                for group in groups
            ],
            parent=course,
            type_=Grouping.Type.BLACKBOARD_GROUP,
        )

    def group_set(self, tool_consumer_instance_guid, resource_link_id):
        return (
            self.request.find_service(name="assignment")
            .get(
                tool_consumer_instance_guid,
                resource_link_id,
            )
            .extra["group_set_id"]
        )

    def get_course(self, course_id, tool_consumer_instance_guid):
        course_service = self.request.find_service(name="course")
        return course_service.get(
            course_service.generate_authority_provided_id(
                tool_consumer_instance_guid, course_id
            )
        )
