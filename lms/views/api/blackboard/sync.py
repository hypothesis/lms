from pyramid.view import view_config

from lms.models import Grouping
from lms.security import Permissions
from lms.services import UserService
from lms.validation import APISyncBlackboardSchema


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
        schema=APISyncBlackboardSchema,
    )
    def sync(self):
        params = self.request.parsed_params["data"]
        tool_consumer_instance_guid = params["lms"]["tool_consumer_instance_guid"]
        resource_link_id = params["assignment"]["resource_link_id"]
        group_info = params["group_info"]
        grading_student_id = params.get("gradingStudentId")

        group_set_id = self.group_set(tool_consumer_instance_guid, resource_link_id)
        course = self.get_course(
            tool_consumer_instance_guid, params["course"]["context_id"]
        )

        groups = self.get_blackboard_groups(course, group_set_id, grading_student_id)

        self.request.find_service(name="lti_h").sync(groups, group_info)
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

        groups = self.blackboard_api.group_set_groups(course.lms_id, group_set_id)
        return self.to_groups_groupings(course, groups)

    def group_set(self, tool_consumer_instance_guid, resource_link_id):
        return (
            self.request.find_service(name="assignment")
            .get(tool_consumer_instance_guid, resource_link_id)
            .extra["group_set_id"]
        )

    def to_groups_groupings(self, course, groups):
        return [
            self.grouping_service.upsert_with_parent(
                tool_consumer_instance_guid=course.application_instance.tool_consumer_instance_guid,
                lms_id=group["id"],
                lms_name=group["name"],
                parent=course,
                type_=Grouping.Type.BLACKBOARD_GROUP,
                extra={"group_set_id": group["groupSetId"]},
            )
            for group in groups
        ]

    def get_course(self, tool_consumer_instance_guid, course_id):
        course_service = self.request.find_service(name="course")
        return course_service.get(
            course_service.generate_authority_provided_id(
                tool_consumer_instance_guid, course_id
            )
        )
