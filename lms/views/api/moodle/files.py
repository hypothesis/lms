import re

from pyramid.view import view_config

from lms.security import Permissions
from lms.services.moodle import MoodleAPIClient
from lms.services.exceptions import FileNotFoundInCourse
from lms.views import helpers

DOCUMENT_URL_REGEX = re.compile(r"moodle:\/\/file\/url\/(?P<url>.*)")


@view_config(
    request_method="GET",
    route_name="moodle_api.courses.files.list",
    renderer="json",
    permission=Permissions.API,
)
def list_files(_context, request):
    """Return the list of files in the given course."""
    return request.find_service(MoodleAPIClient).list_files(
        request.matchdict["course_id"]
    )


@view_config(
    request_method="GET",
    route_name="moodle_api.courses.files.via_url",
    renderer="json",
    permission=Permissions.API,
)
def via_url(_context, request):
    api_client = request.find_service(MoodleAPIClient)

    document_url = request.params["document_url"]
    url = DOCUMENT_URL_REGEX.search(document_url)["url"]
    return {
        "via_url": helpers.via_url(
            request, url, content_type="pdf", query={"token": api_client._token}
        )
    }
