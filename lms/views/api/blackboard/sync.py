from pyramid.view import view_config

from lms.security import Permissions
from lms.validation import APIBlackboardSyncSchema


class Sync:
    def __init__(self, request):
        self.request = request
        self.grouping_service = self.request.find_service(name="grouping")

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
            self.request.parsed_params["assignment"]["group_set_id"],
            self.request.parsed_params.get("gradingStudentId"),
        )

        self.request.find_service(name="lti_h").sync(
            groups, self.request.parsed_params["group_info"]
        )
        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    def get_course(self, course_id):
        return self.request.find_service(name="course").get_by_context_id(course_id)
