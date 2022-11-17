from pyramid.view import view_config

from lms.security import Permissions
from lms.services.d2l_api import D2LAPIClient


@view_config(
    request_method="GET",
    permission=Permissions.API,
    renderer="json",
    route_name="d2l_api.courses.group_sets.list",
)
def course_group_sets(_context, request):
    return request.find_service(D2LAPIClient).course_group_sets(
        org_unit=request.matchdict["course_id"]
    )
