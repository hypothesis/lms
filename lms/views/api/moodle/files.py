import re
from logging import getLogger

from pyramid.view import view_config

from lms.security import Permissions
from lms.services.exceptions import FileNotFoundInCourse
from lms.services.moodle import MoodleAPIClient
from lms.views import helpers

LOG = getLogger(__name__)

DOCUMENT_URL_REGEX = re.compile(
    r"moodle:\/\/file\/course\/(?P<course_id>[^\/]*)\/url\/(?P<url>.*)"
)


@view_config(
    request_method="GET",
    route_name="moodle_api.courses.files.list",
    renderer="json",
    permission=Permissions.API,
)
def list_files(_context, request):
    """Return the list of files in the given course."""
    return request.find_service(MoodleAPIClient).list_files(
        request.matchdict["course_id"]
    )


@view_config(
    request_method="GET",
    route_name="moodle_api.courses.files.via_url",
    renderer="json",
    permission=Permissions.API,
)
def via_url(_context, request):
    course_copy_plugin = request.product.plugin.course_copy

    current_course_id = request.lti_user.lti.course_id
    course = request.find_service(name="course").get_by_context_id(
        current_course_id, raise_on_missing=True
    )

    document_url = request.params["document_url"]
    document_course_id = DOCUMENT_URL_REGEX.search(document_url)["course_id"]
    document_file_id = DOCUMENT_URL_REGEX.search(document_url)["url"]
    effective_file_id = course_copy_plugin.effective_document_id(
        LOG,
        document_url,
        document_course_id,
        document_file_id,
        course,
        current_course_id,
        course.set_mapped_file_id,
        course.get_mapped_file_id,
        "moodle_file_not_found_in_course",
    )

    token = request.find_service(MoodleAPIClient).token
    return {
        "via_url": helpers.via_url(
            request, effective_file_id, content_type="pdf", query={"token": token}
        )
    }
