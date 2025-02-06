"""Proxy API views for files-related Blackboard API endpoints."""

import re

from pyramid.view import view_config, view_defaults

from lms.product.blackboard import Blackboard
from lms.security import Permissions
from lms.services.exceptions import FileNotFoundInCourse
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
        self.course_copy_plugin = request.product.plugin.course_copy

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

        auth_url = self.request.route_url(Blackboard.route.oauth2_authorize)

        for result in results:
            response_result = {
                "display_name": result["name"],
                "updated_at": result["modified"],
                "type": result["type"],
                "parent_id": folder_id,
            }

            if result["type"] == "File" and result.get("mimeType") == "application/pdf":
                response_result["id"] = f"blackboard://content-resource/{result['id']}/"
                response_result["mime_type"] = "application/pdf"
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
        course = self.request.find_service(name="course").get_by_context_id(
            course_id, raise_on_missing=True
        )

        document_url = self.request.params["document_url"]
        document_url_match = DOCUMENT_URL_REGEX.search(document_url)
        assert document_url_match  # noqa: S101
        file_id = course.get_mapped_file_id(document_url_match["file_id"])
        try:
            if self.request.lti_user.is_instructor:  # noqa: SIM102
                if not self.course_copy_plugin.is_file_in_course(course_id, file_id):
                    raise FileNotFoundInCourse(  # noqa: TRY301
                        "blackboard_file_not_found_in_course",  # noqa: EM101
                        file_id,
                    )
            public_url = self.blackboard_api_client.public_url(course_id, file_id)

        except FileNotFoundInCourse:
            found_file = self.course_copy_plugin.find_matching_file_in_course(
                file_id, course_id
            )
            if not found_file:
                raise

            # Try again to return a public URL, this time using found_file_id.
            public_url = self.blackboard_api_client.public_url(
                course_id, found_file.lms_id
            )

            # Store a mapping so we don't have to re-search next time.
            course.set_mapped_file_id(file_id, found_file.lms_id)

        via_url = helpers.via_url(self.request, public_url, content_type="pdf")
        return {"via_url": via_url}
