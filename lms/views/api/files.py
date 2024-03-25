from pyramid.view import view_config

from lms.security import Permissions


@view_config(
    request_method="GET",
    route_name="api.courses.files.list",
    renderer="json",
    permission=Permissions.API,
)
def list_files(_context, request):
    return request.product.api_client.list_files(request.matchdict["course_id"])
