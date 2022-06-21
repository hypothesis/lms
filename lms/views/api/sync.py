from marshmallow import INCLUDE, Schema
from pyramid.view import view_config
from webargs import fields

from lms.security import Permissions
from lms.validation._base import PyramidRequestSchema


class APISyncSchema(PyramidRequestSchema):
    class LMS(Schema):
        tool_consumer_instance_guid = fields.Str(required=True)
        product = fields.Str(required=True)

    class Course(Schema):
        context_id = fields.Str(required=True)
        custom_canvas_course_id = fields.Str(required=False, allow_none=True)
        group_set_id = fields.Str(required=False, allow_none=True)

    class Assignment(Schema):
        resource_link_id = fields.Str(required=True)

    class GroupInfo(Schema):
        class Meta:
            unknown = INCLUDE

    lms = fields.Nested(LMS, required=True)
    course = fields.Nested(Course, required=True)
    assignment = fields.Nested(Assignment, required=True)
    group_info = fields.Nested(GroupInfo, required=True)

    gradingStudentId = fields.Str(required=False, allow_none=True)


class Sync:
    def __init__(self, request):
        self.request = request
        self.grouping_service = self.request.find_service(name="grouping")

    @view_config(
        route_name="api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
        schema=APISyncSchema,
    )
    def sync(self):
        course_id = self.request.parsed_params["course"]["context_id"]
        course = self.request.find_service(name="course").get_by_context_id(course_id)

        if group_set_id := self.request.parsed_params["course"].get("group_set_id"):
            groupings = self.grouping_service.get_groups(
                self.request.user,
                self.request.lti_user,
                course,
                group_set_id,
                self.request.parsed_params.get("gradingStudentId"),
            )
        else:
            groupings = self.grouping_service.get_sections(
                self.request.user,
                self.request.lti_user,
                course,
                self.request.parsed_params.get("gradingStudentId"),
            )

        self._sync_to_h(groupings)

        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groupings]

    def _sync_to_h(self, groups):
        lti_h_svc = self.request.find_service(name="lti_h")
        group_info = self.request.json["group_info"]
        lti_h_svc.sync(groups, group_info)
