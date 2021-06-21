"""Proxy API views for files-related Blackboard API endpoints."""
import re

from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import HTTPError
from lms.views import helpers
from lms.views.api.blackboard._schemas import (
    BlackboardListFilesSchema,
    BlackboardPublicURLSchema,
)
from lms.views.api.blackboard.exceptions import BlackboardFileNotFoundInCourse

#: A regex for parsing just the file_id part out of one of our custom
#: blackboard://content-resource/<file_id>/ URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"blackboard:\/\/content-resource\/(?P<file_id>[^\/]*)\/"
)


@view_defaults(permission=Permissions.API, renderer="json")
class BlackboardFilesAPIViews:
    def __init__(self, request):
        self.request = request
        self.blackboard_api_client = request.find_service(name="blackboard_api_client")

    @view_config(request_method="GET", route_name="blackboard_api.courses.files.list")
    def list_files(self):
        """Return the list of files in the given course."""
        course_id = self.request.matchdict["course_id"]
        response = self.blackboard_api_client.request(
            "GET", f"courses/uuid:{course_id}/resources"
        )
        return BlackboardListFilesSchema(response).parse()

    @view_config(request_method="GET", route_name="blackboard_api.files.via_url")
    def via_url(self):
        """Return the Via URL for annotating the given Blackboard file."""

        course_id = self.request.matchdict["course_id"]
        document_url = self.request.params["document_url"]

        file_id = DOCUMENT_URL_REGEX.search(document_url)["file_id"]

        try:
            response = self.blackboard_api_client.request(
                "GET", f"courses/uuid:{course_id}/resources/{file_id}"
            )
        except HTTPError as err:
            if err.response.status_code == 404:
                raise BlackboardFileNotFoundInCourse(file_id) from err
            raise

        public_url = BlackboardPublicURLSchema(response).parse()

        via_url = helpers.via_url(self.request, public_url, content_type="pdf")

        return {"via_url": via_url}
