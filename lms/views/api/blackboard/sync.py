from pyramid.view import view_config

from lms.security import Permissions
from lms.validation import APIBlackboardSyncSchema


class Sync:
    def __init__(self, request):
        self.request = request
        self.grouping_service = self.request.find_service(name="grouping")

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
        groups = self.grouping_service.get_groups(
            self.request.user,
            self.request.lti_user,
            self.get_course(self.request.parsed_params["course"]["context_id"]),
            self.group_set(),
            self.request.parsed_params.get("gradingStudentId"),
        )

        self.sync_to_h(groups)
        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    def group_set(self):
        return (
            self.request.find_service(name="assignment")
            .get_assignment(
                self.tool_consumer_instance_guid,
                self.request.parsed_params["assignment"]["resource_link_id"],
            )
            .extra["group_set_id"]
        )

    def sync_to_h(self, groups):
        lti_h_svc = self.request.find_service(name="lti_h")
        group_info = self.request.parsed_params["group_info"]
        lti_h_svc.sync(groups, group_info)

    def get_course(self, course_id):
        return self.request.find_service(name="course").get_by_context_id(course_id)
