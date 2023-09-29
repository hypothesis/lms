from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services.canvas import CanvasService


@view_defaults(permission=Permissions.API, renderer="json")
class PagesAPIViews:
    def __init__(self, request):
        self.request = request
        self.canvas = request.find_service(CanvasService)

    @view_config(request_method="GET", route_name="canvas_api.courses.pages.list")
    def list_pages(self):
        """
        Return the list of pages in the given course.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        course_id = self.request.matchdict["course_id"]
        return [
            {
                "id": f"canvas://page/course/{course_id}/page_id/{page.id}",
                "lms_id": page.id,
                "display_name": page.title,
                "type": "Page",
                "updated_at": page.updated_at,
            }
            for page in self.canvas.api.pages.list(course_id)
        ]
