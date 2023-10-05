import re

from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services.canvas import CanvasService
from lms.validation.authentication import BearerTokenSchema
from lms.views import helpers

# A regex for parsing the COURSE_ID and PAGE_ID parts out of one of our custom
# canvas://file/course/COURSE_ID/page_id/PAGE_ID URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"canvas:\/\/page\/course\/(?P<course_id>[^\/]*)\/page_id\/(?P<page_id>[^\/]*)"
)


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
        pages = [
            {
                "id": f"canvas://page/course/{course_id}/page_id/{page.id}",
                "lms_id": page.id,
                "display_name": page.title,
                "type": "Page",
                "updated_at": page.updated_at,
            }
            for page in self.canvas.api.pages.list(course_id)
        ]
        return sorted(pages, key=lambda page: page["display_name"].lower())

    @view_config(request_method="GET", route_name="canvas_api.pages.via_url")
    def via_url(self):
        application_instance = self.request.lti_user.application_instance
        assignment = self.request.find_service(name="assignment").get_assignment(
            application_instance.tool_consumer_instance_guid,
            self.request.lti_user.lti.assignment_id,
        )

        # We build a token to authorize the view that fetches the actual
        # canvas pages content as the user making this request.
        auth_token = BearerTokenSchema(self.request).authorization_param(
            self.request.lti_user
        )
        return {
            "via_url": helpers.via_url(
                self.request,
                self.request.route_url(
                    "canvas_api.pages.proxy",
                    _query={
                        "document_url": assignment.document_url,
                        "authorization": auth_token,
                    },
                ),
            )
        }

    @view_config(
        request_method="GET",
        route_name="canvas_api.pages.proxy",
        renderer="lms:templates/api/canvas/page.html.jinja2",
    )
    def proxy(self):
        """Proxy the contents of a canvas page."""
        document_url_match = DOCUMENT_URL_REGEX.search(
            self.request.params["document_url"]
        )
        course_id = document_url_match["course_id"]
        page = self.canvas.api.pages.page(course_id, document_url_match["page_id"])
        return {
            "canonical_url": page.canonical_url(
                self.request.lti_user.application_instance.lms_host(), course_id
            ),
            "title": page.title,
            "body": page.body,
        }
