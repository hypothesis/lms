from pyramid.view import view_config

from lms.security import Permissions


@view_config(
    request_method="GET",
    permission=Permissions.API,
    renderer="json",
    route_name="api.courses.files.list",
)
@view_config(
    request_method="GET",
    permission=Permissions.API,
    route_name="api.courses.folders.files.list",
    renderer="json",
)
def course_group_sets(_context, request):
    course_id = request.matchdict["course_id"]
    folder_id = request.matchdict.get("folder_id")
    return request.product.plugin.grouping.get_group_sets(course_id, folder_id)
