"""Proxy API views for group-related Canvas API endpoints."""
from pyramid.view import view_config, view_defaults

from lms.security import Permissions


@view_defaults(permission=Permissions.API, renderer="json")
class GroupsAPIViews:
    def __init__(self, request):
        self.request = request
        self.canvas_api_client = request.find_service(name="canvas_api_client")

    @view_config(
        request_method="GET", route_name="canvas_api.courses.group_categories.list"
    )
    def course_group_categories(self):
        """
        Return the list of group categories in the given course.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        return self.canvas_api_client.course_group_categories(
            self.request.matchdict["course_id"]
        )
