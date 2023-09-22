import re

from pyramid.view import view_config, view_defaults
from pyramid.response import Response

from lms.validation.authentication import BearerTokenSchema
from lms.security import Permissions
from lms.services.canvas import CanvasService
from lms.views import helpers
from urllib import parse
from h_vialib import ContentType

#: A regex for parsing the COURSE_ID and FILE_ID parts out of one of our custom
#: canvas://file/course/COURSE_ID/file_id/FILE_ID URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"canvas:\/\/page\/course\/(?P<course_id>[^\/]*)\/page_id\/(?P<page_id>[^\/]*)"
)


@view_defaults(permission=Permissions.API, renderer="json")
class PageAPIViews:
    def __init__(self, request):
        self.request = request
        self.canvas = request.find_service(CanvasService)

    @view_config(request_method="GET", route_name="canvas_api.courses.pages.list")
    def list_pages(self):
        """
        Return the list of files in the given course.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        course_id = self.request.matchdict["course_id"]
        return [
            {
                "id": f"canvas://page/course/{course_id}/page_id/{page.id}",
                "lms_id": page.id,
                "display_name": page.title,
                "type": "File",
                "updated_at": page.updated_at,
            }
            for page in self.canvas.api.pages.list(course_id)
        ]

    @view_config(request_method="GET", route_name="canvas_api.pages.via_url")
    def via_url(self):
        application_instance = self.request.lti_user.application_instance
        assignment = self.request.find_service(name="assignment").get_assignment(
            application_instance.tool_consumer_instance_guid,
            self.request.matchdict["resource_link_id"],
        )
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

    """
    @view_config(request_method="GET", route_name="canvas_api.pages.via_url")
    def via_url(self):
        application_instance = self.request.lti_user.application_instance
        assignment = self.request.find_service(name="assignment").get_assignment(
            application_instance.tool_consumer_instance_guid,
            self.request.matchdict["resource_link_id"],
        )

        document_url_match = DOCUMENT_URL_REGEX.search(assignment.document_url)
        public_url = self.canvas.api.pages.public_url(
            document_url_match["course_id"], document_url_match["page_id"]
        )

        access_token = self.request.find_service(name="oauth2_token").get().access_token
        headers = {"Authorization": f"Bearer {access_token}"}
        return {
            "via_url": helpers.via_url(
                self.request,
                assignment.document_url
                + "?"
                + parse.urlencode({"api_url": public_url}),
                content_type=ContentType.CANVAS_PAGE,
                headers=headers,
            )
        }
    """

    @view_config(request_method="GET", route_name="canvas_api.pages.proxy")
    def proxy(self):
        document_url_match = DOCUMENT_URL_REGEX.search(
            self.request.params["document_url"]
        )
        page = self.canvas.api.pages.page(
            document_url_match["course_id"], document_url_match["page_id"]
        )

        return Response(body=page.body)

        """
        access_token = self.request.find_service(name="oauth2_token").get().access_token
        headers = {"Authorization": f"Bearer {access_token}"}
        return {
            "via_url": helpers.via_url(
                self.request,
                assignment.document_url
                + "?"
                + parse.urlencode({"api_url": public_url}),
                content_type=ContentType.CANVAS_PAGE,
                headers=headers,
            )
        }
        """
