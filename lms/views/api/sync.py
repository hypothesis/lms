from marshmallow import INCLUDE, Schema
from pyramid.view import view_config
from webargs import fields

from lms.security import Permissions
from lms.validation._base import PyramidRequestSchema


class APISyncSchema(PyramidRequestSchema):
    class LMS(Schema):
        product = fields.Str(required=True)

    class GroupInfo(Schema):
        class Meta:
            unknown = INCLUDE

    lms = fields.Nested(LMS, required=True)
    context_id = fields.Str(required=True)
    group_set_id = fields.Str(required=False, allow_none=True)
    group_info = fields.Nested(GroupInfo, required=True)

    gradingStudentId = fields.Str(required=False, allow_none=True)


@view_config(
    route_name="api.sync",
    request_method="POST",
    renderer="json",
    permission=Permissions.API,
    schema=APISyncSchema,
)
def sync(request):
    grouping_service = request.find_service(name="grouping")
    course = request.find_service(name="course").get_by_context_id(
        context_id=request.parsed_params["context_id"]
    )
    grading_student_id = request.parsed_params.get("gradingStudentId")

    if group_set_id := request.parsed_params.get("group_set_id"):
        groupings = grouping_service.get_groups(
            user=request.user,
            lti_user=request.lti_user,
            course=course,
            grading_student_id=grading_student_id,
            group_set_id=group_set_id,
        )

    else:
        groupings = grouping_service.get_sections(
            user=request.user,
            lti_user=request.lti_user,
            course=course,
            grading_student_id=grading_student_id,
        )

    request.find_service(name="lti_h").sync(
        groupings, request.parsed_params["group_info"]
    )
    authority = request.registry.settings["h_authority"]
    return [group.groupid(authority) for group in groupings]
