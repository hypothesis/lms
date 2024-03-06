from pyramid.view import view_config

from lms.security import Permissions
from lms.services.lms_api import LMSAPI


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
    return request.find_service(LMSAPI).list_files(course_id, folder_id)
