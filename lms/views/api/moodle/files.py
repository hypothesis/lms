import re

from pyramid.view import view_config

from lms.security import Permissions
from lms.services.moodle import MoodleAPIClient
from lms.views import helpers

DOCUMENT_URL_REGEX = re.compile(r"moodle:\/\/file\/url\/(?P<url>.*)")


@view_config(
    request_method="GET",
    route_name="moodle_api.courses.files.via_url",
    renderer="json",
    permission=Permissions.API,
)
def via_url(_context, request):
    token = request.find_service(MoodleAPIClient).token

    document_url = request.params["document_url"]
    url = DOCUMENT_URL_REGEX.search(document_url)["url"]
    return {
        "via_url": helpers.via_url(
            request, url, content_type="pdf", query={"token": token}
        )
    }
