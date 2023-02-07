from pyramid.view import view_config
from lms.validation._base import PyramidRequestSchema
from marshmallow import Schema
from webargs import fields

from lms.security import Permissions


class APIGroupSetsSchema(PyramidRequestSchema):
    class LMS(Schema):
        product = fields.Str(required=True)

    context_id = fields.Str(required=True)


@view_config(
    request_method="POST",
    permission=Permissions.API,
    renderer="json",
    route_name="api.courses.group_sets.list",
    schema=APIGroupSetsSchema,
)
def course_group_sets(_context, request):
    course = request.find_service(name="course").get_by_context_id(
        context_id=request.parsed_params["context_id"]
    )

    return request.product.plugin.grouping.get_group_sets(
        course, request.matchdict["course_id"]
    )
