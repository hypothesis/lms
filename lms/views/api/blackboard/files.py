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
    @view_config(
        request_method="GET", route_name="blackboard_api.courses.folders.files.list"
    )
    def list_files(self):
        """Return the list of files in the given course or folder."""

        course_id = self.request.matchdict["course_id"]
        folder_id = self.request.matchdict.get("folder_id")

        results = self.blackboard_api_client.list_files(course_id, folder_id)

        response_results = []

        auth_url = self.request.route_url("blackboard_api.oauth.authorize")

        for result in results:
            response_result = {
                "display_name": result["name"],
                "updated_at": result["modified"],
                "type": result["type"],
                "parent_id": folder_id,
            }

            if result["type"] == "File" and result.get("mimeType") == "application/pdf":
                response_result["id"] = f"blackboard://content-resource/{result['id']}/"
                response_results.append(response_result)
            elif result["type"] == "Folder":
                response_result["id"] = result["id"]
                response_result["contents"] = {
                    "authUrl": auth_url,
                    "path": self.request.route_path(
                        "blackboard_api.courses.folders.files.list",
                        course_id=course_id,
                        folder_id=result["id"],
                    ),
                }
                response_results.append(response_result)

        return response_results

    @view_config(request_method="GET", route_name="blackboard_api.files.via_url")
    def via_url(self):
        """Return the Via URL for annotating the given Blackboard file."""

        course_id = self.request.matchdict["course_id"]
        document_url = self.request.params["document_url"]
        file_id = DOCUMENT_URL_REGEX.search(document_url)["file_id"]

        public_url = self.blackboard_api_client.public_url(course_id, file_id)

        via_url = helpers.via_url(self.request, public_url, content_type="pdf")

        return {"via_url": via_url}
