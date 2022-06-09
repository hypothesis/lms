from marshmallow import INCLUDE, Schema
from pyramid.view import view_config
from webargs import fields

from lms.security import Permissions
from lms.services import ProductGroupingService
from lms.validation._base import PyramidRequestSchema


class APISyncSchema(PyramidRequestSchema):
    class LMS(Schema):
        tool_consumer_instance_guid = fields.Str(required=True)

    class Course(Schema):
        context_id = fields.Str(required=True)

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
        self.blackboard_api = self.request.find_service(name="blackboard_api_client")

        self.tool_consumer_instance_guid = self.request.parsed_params["lms"][
            "tool_consumer_instance_guid"
        ]

        self.product_grouping: ProductGroupingService = self.request.find_service(
            ProductGroupingService
        )

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

        if group_set_id := self.request.parsed_params("group_set_id"):
            groupings = self.product_grouping.get_groups(course, group_set_id)
        else:
            groupings = self.product_grouping.get_sections(
                course, self.request.parsed_params
            )

        self._sync_to_h(groupings)

        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groupings]

    def _sync_to_h(self, groups):
        lti_h_svc = self.request.find_service(name="lti_h")
        group_info = self.request.json["group_info"]
        lti_h_svc.sync(groups, group_info)
