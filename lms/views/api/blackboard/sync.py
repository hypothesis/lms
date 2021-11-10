from pyramid.view import view_config

from lms.security import Permissions
from lms.services import CanvasAPIError
from lms.views import (
    CanvasGroupSetEmpty,
    CanvasGroupSetNotFound,
    CanvasStudentNotInGroup,
)

from lms.models import GroupingMembership, User
from lms.models._hashed_id import hashed_id
from lms.services import UserService

from sqlalchemy.orm import joinedload


class Sync:
    def __init__(self, request):
        self._request = request
        self._grouping_service = self._request.find_service(name="grouping")
        self._blackboard_api = self._request.find_service(name="blackboard_api_client")
        self._assignment_service = self._request.find_service(name="assignment")
        self._user_service = self._request.find_service(UserService)
        self._course_service = self._request.find_service(name="course")

    @view_config(
        route_name="blackboard_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def sync(self):
        groups = self._get_blackboard_groups()

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
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        if lti_user.is_learner:
            # For learners, the groups they belong within the course
            learner_groups = self._blackboard_api.course_groups(
                self._request.json["course"]["context_id"],
                group_set_id,
            )
            if not learner_groups:
                raise CanvasStudentNotInGroup(group_set=group_set_id)

            groups = self._to_groups_groupings(learner_groups)
            self._grouping_service.upsert_grouping_memberships(
                self._user_service.store_lti_user(lti_user), groups
            )
            return groups

        if grading_student_id := self._request.json.get("gradingStudentId"):
            db = self._grouping_service._db

            authority_provided_id = hashed_id(tool_guid, course_id)
            course = self._course_service.get(authority_provided_id)
            return [
                gm.grouping
                for gm in db.query(GroupingMembership)
                .join(User)
                .filter(
                    GroupingMembership.grouping_id.in_([g.id for g in course.children]),
                    User.user_id == grading_student_id,
                )
                .options(joinedload("grouping"))
            ]

        try:
            # If not grading return all the groups in the course so the teacher can toggle between them.
            groups = self._blackboard_api.group_category_groups(course_id, group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise CanvasGroupSetNotFound(group_set=group_set_id) from canvas_api_error

        if not groups:
            raise CanvasGroupSetEmpty(group_set=group_set_id)

        return self._to_groups_groupings(groups)

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
