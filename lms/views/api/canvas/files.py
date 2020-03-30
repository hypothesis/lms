"""Proxy API views for files-related Canvas API endpoints."""
from pyramid.view import view_config, view_defaults

from lms.views import helpers


@view_defaults(permission="canvas_api", renderer="json")
class FilesAPIViews:
    def __init__(self, request):
        self.request = request
        self.canvas_api_client = request.find_service(name="canvas_api_client")

    @view_config(request_method="GET", route_name="canvas_api.courses.files.list")
    def list_files(self):
        """
        Return the list of files in the given course.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        return self.canvas_api_client.list_files(self.request.matchdict["course_id"])

    @view_config(request_method="GET", route_name="canvas_api.files.via_url")
    def via_url(self):
        """
        Return the Via URL for annotating the given Canvas file.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        public_url = self.canvas_api_client.public_url(
            self.request.matchdict["file_id"]
        )
        via_url = helpers.via_url(self.request, public_url)
        return {"via_url": via_url}
