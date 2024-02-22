import logging
import re

from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services.canvas import CanvasService
from lms.services.exceptions import CanvasAPIError, FileNotFoundInCourse
from lms.services.moodle import MoodleAPIClient
from lms.validation.authentication import BearerTokenSchema
from lms.views import helpers

LOG = logging.getLogger(__name__)

# A regex for parsing the COURSE_ID and PAGE_ID parts out of one of our custom
# canvas://page/course/COURSE_ID/page_id/PAGE_ID URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"moodle:\/\/page\/course\/(?P<course_id>[^\/]*)\/page_id\/(?P<page_id>[^\/]*)"
)


class PageNotFoundInCourse(FileNotFoundInCourse):
    pass


@view_defaults(permission=Permissions.API, renderer="json")
class PagesAPIViews:
    def __init__(self, request):
        self.request = request
        self.api = request.find_service(MoodleAPIClient)

    @view_config(request_method="GET", route_name="moodle_api.courses.pages.list")
    def list_pages(self):
        """
        Return the list of pages in the given course.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        course_id = self.request.matchdict["course_id"]
        pages = [
            {
                "id": f"moodle://page/course/{course_id}/page_id/{page['id']}",
                "lms_id": page["id"],
                "display_name": page["name"],
                "type": "Page",
                "updated_at": page["timemodified"],
            }
            for page in self.api.list_pages(course_id)
        ]
        return sorted(pages, key=lambda page: page["display_name"].lower())

    @view_config(request_method="GET", route_name="moodle_api.pages.via_url")
    def via_url(self):
        current_course = self.request.find_service(name="course").get_by_context_id(
            self.request.lti_user.lti.course_id, raise_on_missing=True
        )
        assignment = self.request.find_service(name="assignment").get_assignment(
            self.request.lti_user.application_instance.tool_consumer_instance_guid,
            self.request.lti_user.lti.assignment_id,
        )
        document_url = assignment.document_url
        document_course_id, document_page_id = self._parse_document_url(document_url)

        # We build a token to authorize the view that fetches the actual
        # canvas pages content as the user making this request.
        auth_token = BearerTokenSchema(self.request).authorization_param(
            self.request.lti_user
        )

        return {
            "via_url": helpers.via_url(
                self.request,
                self.request.route_url(
                    "moodle_api.pages.proxy",
                    _query={
                        "course_id": current_course.lms_id,
                        "page_id": document_page_id,
                        "authorization": auth_token,
                    },
                ),
            )
        }

    @view_config(
        request_method="GET",
        route_name="moodle_api.pages.proxy",
        renderer="lms:templates/api/canvas/page.html.jinja2",
    )
    def proxy(self):
        course_id, page_id = (
            self.request.params["course_id"],
            self.request.params["page_id"],
        )

        page = self.api.page(course_id, page_id)
        body = page["body"]

        body = body.replace("/webservice/pluginfile.php/", "/pluginfile.php/")
        return {
            "canonical_url": f"{self.request.lti_user.application_instance.lms_host()}/mod/page/view.php?id={page['course_module']}",
            "title": page["title"],
            "body": body,
        }

    @staticmethod
    def _parse_document_url(document_url):
        document_url_match = DOCUMENT_URL_REGEX.search(document_url)
        course_id = document_url_match["course_id"]
        page_id = document_url_match["page_id"]

        return course_id, page_id
