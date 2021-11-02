from pyramid.view import view_config

from lms.security import Permissions
from lms.services import CanvasAPIError
from lms.views import (
    CanvasGroupSetEmpty,
    CanvasGroupSetNotFound,
    CanvasStudentNotInGroup,
)


class Sync:
    def __init__(self, request):
        self._request = request
        self._grouping_service = self._request.find_service(name="grouping")
        self._blackboard_api = self._request.find_service(name="blackboard_api_client")
        self._assignment_service = self._request.find_service(name="assignment")

    @view_config(
        route_name="blackboard_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def sync(self):
        groups = self._to_groups_groupings(self._get_blackboard_groups())

        self._sync_to_h(groups)

        authority = self._request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    def group_set(self):
        tool_consumer_instance_guid = self._request.json["lms"][
            "tool_consumer_instance_guid"
        ]
        resource_link_id = self._request.json["course"]["resource_link_id"]
        return self._assignment_service.get(
            tool_consumer_instance_guid, resource_link_id
        ).extra["group_set"]

    def _get_blackboard_groups(self):
        lti_user = self._request.lti_user
        group_set_id = self.group_set()
        course_id = self._request.json["course"]["context_id"]
        if lti_user.is_learner:
            # For learners, the groups they belong within the course
            learner_groups = self._blackboard_api.course_groups(
                self._request.json["course"]["context_id"],
                group_set_id,
            )
            if not learner_groups:
                raise CanvasStudentNotInGroup(group_set=group_set_id)

            return learner_groups

        if grading_student_id := self._request.json.get("gradingStudentId"):
            return self._blackboard_api.user_groups(
                course_id, grading_student_id, group_set_id
            )

        try:
            # If not grading return all the groups in the course so the teacher can toggle between them.
            groups = self._blackboard_api.group_category_groups(course_id, group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise CanvasGroupSetNotFound(group_set=group_set_id) from canvas_api_error

        if not groups:
            raise CanvasGroupSetEmpty(group_set=group_set_id)

        return groups

    def _to_groups_groupings(self, groups):
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        context_id = self._request.json["course"]["context_id"]

        return [
            self._grouping_service.upsert_canvas_group(
                tool_consumer_instance_guid=tool_guid,
                context_id=context_id,
                group_name=group["name"],
                group_id=group["id"],
                group_set_id=group["groupSetId"],
            )
            for group in groups
        ]

    def _sync_to_h(self, groups):
        lti_h_svc = self._request.find_service(name="lti_h")
        group_info = self._request.json["group_info"]
        lti_h_svc.sync(groups, group_info)
