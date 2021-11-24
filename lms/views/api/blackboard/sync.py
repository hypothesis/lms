from pyramid.view import view_config

from lms.models import Grouping
from lms.security import Permissions


class Sync:
    def __init__(self, request):
        self._request = request
        self._assignment_service = self._request.find_service(name="assignment")
        self._grouping_service = self._request.find_service(name="grouping")
        self._course_service = self._request.find_service(name="course")
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
        group_set_id = self._group_set()
        course_id = self._request.json["course"]["context_id"]
        groups = self._blackboard_api.group_set_groups(course_id, group_set_id)

        return self._to_groups_groupings(groups)

    def _group_set(self):
        return self._assignment_service.get(
            self._tool_consumer_instance_guid,
            self._request.json["assignment"]["resource_link_id"],
        ).extra["group_set_id"]

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
        return self._course_service.get(
            self._course_service.generate_authority_provided_id(
                self._tool_consumer_instance_guid,
                self._request.json["course"]["context_id"],
            )
        )
