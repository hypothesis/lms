import logging
import re

from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services.canvas import CanvasService
from lms.services.exceptions import CanvasAPIError, FileNotFoundInCourse
from lms.validation.authentication import BearerTokenSchema
from lms.views import helpers

LOG = logging.getLogger(__name__)

# A regex for parsing the COURSE_ID and PAGE_ID parts out of one of our custom
# canvas://page/course/COURSE_ID/page_id/PAGE_ID URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"canvas:\/\/page\/course\/(?P<course_id>[^\/]*)\/page_id\/(?P<page_id>[^\/]*)"
)


class PageNotFoundInCourse(FileNotFoundInCourse):
    pass


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
        course_copy_plugin = self.request.product.plugin.course_copy
        current_course = self.request.find_service(name="course").get_by_context_id(
            self.request.lti_user.lti.course_id, raise_on_missing=True
        )
        current_course_id = str(
            current_course.extra["canvas"]["custom_canvas_course_id"]
        )
        assignment = self.request.find_service(name="assignment").get_assignment(
            self.request.lti_user.application_instance.tool_consumer_instance_guid,
            self.request.lti_user.lti.assignment_id,
        )
        document_url = assignment.document_url
        document_course_id, document_page_id = self._parse_document_url(document_url)

        effective_page_id = None
        if current_course_id == document_course_id:
            # Not in a course copy scenario, use the IDs from the document_url
            effective_page_id = document_page_id
            LOG.debug("Via URL for page in the same course. %s", document_url)

        mapped_page_id = current_course.get_mapped_page_id(document_page_id)
        if not effective_page_id and mapped_page_id != document_page_id:
            effective_page_id = mapped_page_id
            LOG.debug(
                "Via URL for page already mapped for course copy. Document: %s, course: %s, mapped page_id: %s",
                document_url,
                current_course_id,
                mapped_page_id,
            )

        if not effective_page_id:
            found_page = course_copy_plugin.find_matching_page_in_course(
                document_page_id, current_course_id
            )
            if not found_page:
                # We couldn't fix course copy, there might be something else going on
                # or maybe teacher never launched before a student.
                LOG.debug(
                    "Via URL for page, couldn't find page in the new course. Document: %s, course: %s.",
                    document_url,
                    current_course_id,
                )
                raise PageNotFoundInCourse(
                    "canvas_page_not_found_in_course", document_page_id
                )

            # Store a mapping so we don't have to re-search next time.
            current_course.set_mapped_page_id(document_page_id, found_page.lms_id)
            effective_page_id = found_page.lms_id
            LOG.debug(
                "Via URL for page, found page in the new course. Document: %s, course: %s, new page id: %s",
                document_url,
                current_course_id,
                found_page.lms_id,
            )

        # Try to access the page
        # We don't need the  result of this exact call but we accomplishes two things here:
        # We can check that we indeed have access to this page, if we don't we try to fix any course copy related issues.
        # We make sure that we have a recent Oauth2 token to make a request later in the proxying endpoint.
        try:
            _ = self.canvas.api.pages.page(current_course_id, effective_page_id)
        except CanvasAPIError as err:
            raise PageNotFoundInCourse(
                "canvas_page_not_found_in_course", effective_page_id
            ) from err

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
                        "course_id": current_course_id,
                        "page_id": effective_page_id,
                        "authorization": auth_token,
                    },
                ),
                # Disable proxying of iframes. This enables embedded widgets to
                # work if they require authentication or simply aren't compatible
                # with viahtml's proxying.
                #
                # See https://github.com/hypothesis/support/issues/98.
                options={"via.proxy_frames": "0"},
            )
        }

    @view_config(
        request_method="GET",
        route_name="canvas_api.pages.proxy",
        renderer="lms:templates/api/canvas/page.html.jinja2",
    )
    def proxy(self):
        """Proxy the contents of a canvas page."""
        course_id, page_id = (
            self.request.params["course_id"],
            self.request.params["page_id"],
        )

        page = self.canvas.api.pages.page(course_id, page_id)
        return {
            "canonical_url": page.canonical_url(
                self.request.lti_user.application_instance.lms_host(), course_id
            ),
            "title": page.title,
            "body": page.body,
        }

    @staticmethod
    def _parse_document_url(document_url):
        document_url_match = DOCUMENT_URL_REGEX.search(document_url)
        course_id = document_url_match["course_id"]
        page_id = document_url_match["page_id"]

        return course_id, page_id
