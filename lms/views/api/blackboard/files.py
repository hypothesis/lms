"""Proxy API views for files-related Blackboard API endpoints."""
from pyramid.view import view_config, view_defaults

from lms.views.helpers import via_url


@view_defaults(permission="blackboard_api", renderer="json")
class FilesAPIViews:
    def __init__(self, request):
        self.request = request
        self.blackboard_api_client = request.find_service(name="blackboard_api_client")

    @view_config(request_method="GET", route_name="blackboard_api.courses.files.list")
    def list_files(self):
        return self.blackboard_api_client.list_files(
            self.request.matchdict["course_id"]
        )

    @view_config(request_method="GET", route_name="blackboard_api.files.via_url")
    def via_url(self):
        return {
            "via_url": via_url(
                self.request,
                self.blackboard_api_client.public_url(
                    self.request.matchdict["file_id"]
                ),
                content_type="pdf",
            ),
        }
