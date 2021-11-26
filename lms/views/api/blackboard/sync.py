from pyramid.view import view_config

from lms.models import Grouping
from lms.security import Permissions
from lms.services import UserService


class Sync:
    def __init__(self, request):
        self._request = request
        self._grouping_service = self._request.find_service(name="grouping")
        self._blackboard_api = self._request.find_service(name="blackboard_api_client")

        self._tool_consumer_instance_guid = self._request.json["lms"][
            "tool_consumer_instance_guid"
        ]

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

    def _get_blackboard_groups(self):
        lti_user = self._request.lti_user
        group_set_id = self._group_set()
        course_id = self._request.json["course"]["context_id"]

        if lti_user.is_learner:
            user = self._request.find_service(UserService).get(
                self._request.find_service(name="application_instance").get_current(),
                lti_user.user_id,
            )

            learner_groups = self._blackboard_api.course_groups(
                course_id, group_set_id, current_student_own_groups_only=True
            )
            groups = self._to_groups_groupings(learner_groups)
            self._grouping_service.upsert_grouping_memberships(user, groups)
            return groups

        groups = self._blackboard_api.group_set_groups(course_id, group_set_id)

        return self._to_groups_groupings(groups)

    def _group_set(self):
        return (
            self._request.find_service(name="assignment")
            .get(
                self._tool_consumer_instance_guid,
                self._request.json["assignment"]["resource_link_id"],
            )
            .extra["group_set_id"]
        )

    def _to_groups_groupings(self, groups):
        course = self._get_course()

        return [
            self._grouping_service.upsert_with_parent(
                tool_consumer_instance_guid=self._tool_consumer_instance_guid,
                lms_id=group["id"],
                lms_name=group["name"],
                parent=course,
                type_=Grouping.Type.BLACKBOARD_GROUP,
                extra={"group_set_id": group["groupSetId"]},
            )
            for group in groups
        ]

    def _sync_to_h(self, groups):
        lti_h_svc = self._request.find_service(name="lti_h")
        group_info = self._request.json["group_info"]
        lti_h_svc.sync(groups, group_info)

    def _get_course(self):
        course_service = self._request.find_service(name="course")
        return course_service.get(
            course_service.generate_authority_provided_id(
                self._tool_consumer_instance_guid,
                self._request.json["course"]["context_id"],
            )
        )
