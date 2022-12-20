import re
from pyramid.view import view_config
from lms.views import helpers

from lms.security import Permissions
from lms.services.d2l_api import D2LAPIClient


DOCUMENT_URL_REGEX = re.compile(
    r"d2l:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)\/"
)


@view_config(
    request_method="GET",
    route_name="d2l_api.courses.files.list",
    renderer="json",
    permission=Permissions.API,
)
def list_files(_context, request):
    """Return the list of files in the given course."""
    return request.find_service(D2LAPIClient).list_files(request.matchdict["course_id"])


@view_config(
    request_method="GET",
    route_name="d2l_api.courses.files.via_url",
    renderer="json",
    permission=Permissions.API,
)
def via_url(_context, request):
    course_id = request.matchdict["course_id"]
    document_url = request.params["document_url"]
    file_id = DOCUMENT_URL_REGEX.search(document_url)["file_id"]

    public_url = request.find_service(D2LAPIClient).public_url(course_id, file_id)

    access_token = request.find_service(name="oauth2_token").get().access_token
    headers = {"Authorization": f"Bearer {access_token}"}

    via_url = helpers.via_url(request, public_url, content_type="pdf", headers=headers)
    return {"via_url": via_url}
