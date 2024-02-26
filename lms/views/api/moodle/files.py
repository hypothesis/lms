import re

from pyramid.view import view_config

from lms.security import Permissions
from lms.services.moodle import MoodleAPIClient

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
