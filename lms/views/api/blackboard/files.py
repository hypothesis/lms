"""Proxy API views for files-related Blackboard API endpoints."""
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.views import helpers


@view_defaults(permission=Permissions.API, renderer="json")
class BlackboardFilesAPIViews:
    def __init__(self, request):
        self.request = request
        self.blackboard_api_client = request.find_service(name="blackboard_api_client")

    @view_config(request_method="GET", route_name="blackboard_api.courses.files.list")
    def list_files(self):
        """Return the list of files in the given course."""
        return self.blackboard_api_client.list_files(
            self.request.matchdict["course_id"]
        )

    @view_config(request_method="GET", route_name="blackboard_api.files.via_url")
    def via_url(self):
        """Return the Via URL for annotating the given Blackboard file."""

        return {
            "via_url": helpers.via_url(
                self.request,
                self.blackboard_api_client.public_url(
                    self.request.matchdict["course_id"],
                    self.request.params["document_url"],
                ),
                content_type="pdf",
            )
        }
