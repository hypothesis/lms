from pyramid.view import view_config

from lms.security import Permissions


@view_config(
    request_method=["POST", "GET"],
    permission=Permissions.API,
    renderer="json",
    route_name="api.courses.group_sets.list",
)
def course_group_sets(_context, request):
    course = request.find_service(name="course").get_by_context_id(
        request.matchdict["course_id"], raise_on_missing=True
    )
    return request.product.plugin.grouping.get_group_sets(course)
