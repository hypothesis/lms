"""Proxy API views for files-related Blackboard API endpoints."""
import re

from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.views import helpers

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

        files = self.blackboard_api_client.list_files(
            self.request.matchdict["course_id"]
        )

        pdf_files = []

        for file in files:
            if file.get("mimeType") != "application/pdf":
                continue

            pdf_files.append(
                {
                    "id": f"blackboard://content-resource/{file['id']}/",
                    "display_name": file["name"],
                    "updated_at": file["modified"],
                }
            )

        return pdf_files

    @view_config(request_method="GET", route_name="blackboard_api.files.via_url")
    def via_url(self):
        """Return the Via URL for annotating the given Blackboard file."""

        course_id = self.request.matchdict["course_id"]
        document_url = self.request.params["document_url"]
        file_id = DOCUMENT_URL_REGEX.search(document_url)["file_id"]

        public_url = self.blackboard_api_client.public_url(course_id, file_id)

        via_url = helpers.via_url(self.request, public_url, content_type="pdf")

        return {"via_url": via_url}
