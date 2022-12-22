from pyramid.view import view_config

from lms.security import Permissions
from lms.services.d2l_api import D2LAPIClient


@view_config(
    request_method="GET",
    route_name="d2l_api.courses.files.list",
    renderer="json",
    permission=Permissions.API,
)
def list_files(_context, request):
    """Return the list of files in the given course."""
    return request.find_service(D2LAPIClient).list_files(
        org_unit=request.matchdict["course_id"]
    )
