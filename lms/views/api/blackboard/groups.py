from pyramid.view import view_config

from lms.security import Permissions


@view_config(
    request_method="GET",
    permission=Permissions.API,
    renderer="json",
    route_name="blackboard_api.courses.group_sets.list",
)
def course_group_sets(_context, request):
    blackboard_api_client = request.find_service(name="blackboard_api_client")
    return blackboard_api_client.course_group_categories(request.matchdict["course_id"])
