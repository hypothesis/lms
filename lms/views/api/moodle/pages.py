import logging
import re

from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services.exceptions import FileNotFoundInCourse
from lms.services.moodle import MoodleAPIClient
from lms.validation.authentication import BearerTokenSchema
from lms.views import helpers

LOG = logging.getLogger(__name__)

# A regex for parsing the COURSE_ID and PAGE_ID parts out of custom URL
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
        return self.request.find_service(MoodleAPIClient).list_pages(
            self.request.matchdict["course_id"]
        )

    @view_config(request_method="GET", route_name="moodle_api.pages.via_url")
    def via_url(self):
        course_copy_plugin = self.request.product.plugin.course_copy
        current_course_id = self.request.lti_user.lti.course_id

        current_course = self.request.find_service(name="course").get_by_context_id(
            current_course_id, raise_on_missing=True
        )
        assignment = self.request.find_service(name="assignment").get_assignment(
            self.request.lti_user.application_instance.tool_consumer_instance_guid,
            self.request.lti_user.lti.assignment_id,
        )
        document_url = assignment.document_url
        document_course_id, document_page_id = self._parse_document_url(document_url)
        effective_page_id = _effective_page_id(
            course_copy_plugin,
            current_course,
            document_url,
            document_course_id,
            document_page_id,
        )

        # Try to access the page
        # We don't need the result of this exact call but
        # we can check that we have indeed access to this page.
        if not self.api.page(current_course.lms_id, effective_page_id):
            raise PageNotFoundInCourse("moodle_page_not_found_in_course", document_url)

        # We build a token to authorize the view that fetches the actual
        # pages content as the user making this request.
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
                        "page_id": effective_page_id,
                        "authorization": auth_token,
                    },
                ),
                options={
                    # Disable proxying of iframes. This enables embedded widgets to work.
                    "via.proxy_frames": "0",
                    # Images from Moodle need cookie authentication, stop proxying them.
                    "via.proxy_images": "0",
                },
            )
        }

    @view_config(
        request_method="GET",
        route_name="moodle_api.pages.proxy",
        renderer="lms:templates/api/moodle/page.html.jinja2",
    )
    def proxy(self):
        course_id, page_id = (
            self.request.params["course_id"],
            self.request.params["page_id"],
        )

        page = self.api.page(course_id, page_id)
        body = page["body"]

        # The API returns URL to embedded content using "API" URLs
        # which require token authentication.
        # Replace them by URL that work using the user's cookie with Moodle.
        body = body.replace("/webservice/pluginfile.php/", "/pluginfile.php/")
        return {
            "canonical_url": f"{self.request.lti_user.application_instance.lms_host()}/mod/page/view.php?id={page['course_module']}",
            "title": page["title"],
            "body": body,
        }

    @staticmethod
    def _parse_document_url(document_url):
        document_url_match = DOCUMENT_URL_REGEX.search(document_url)
        assert document_url_match
        course_id = document_url_match["course_id"]
        page_id = document_url_match["page_id"]

        return course_id, page_id


def _effective_page_id(
    course_copy_plugin, course, document_url, document_course_id, document_page_id
):
    if course.lms_id == document_course_id:
        # Not in a course copy scenario, use the IDs from the document_url
        LOG.debug("Via URL for page in the same course. %s", document_url)
        return document_page_id

    mapped_page_id = course.get_mapped_page_id(document_page_id)
    if mapped_page_id != document_page_id:
        LOG.debug(
            "Via URL for page already mapped for course copy. Document: %s, course: %s, mapped page_id: %s",
            document_url,
            course.lms_id,
            mapped_page_id,
        )
        return mapped_page_id

    found_page = course_copy_plugin.find_matching_page_in_course(
        document_page_id, course.lms_id
    )
    if not found_page:
        # We couldn't fix course copy, there might be something else going on
        # or maybe teacher never launched before a student.
        LOG.debug(
            "Via URL for page, couldn't find page in the new course. Document: %s, course: %s.",
            document_url,
            course.lms_id,
        )
        raise PageNotFoundInCourse("moodle_page_not_found_in_course", document_page_id)

    # Store a mapping so we don't have to re-search next time.
    course.set_mapped_page_id(document_page_id, found_page.lms_id)
    LOG.debug(
        "Via URL for page, found page in the new course. Document: %s, course: %s, new page id: %s",
        document_url,
        course.lms_id,
        found_page.lms_id,
    )
    return found_page.lms_id
