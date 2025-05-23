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
    api = request.find_service(MoodleAPIClient)
    course_copy_plugin = request.product.plugin.course_copy

    current_course_id = request.lti_user.lti.course_id
    course = request.find_service(name="course").get_by_context_id(
        current_course_id, raise_on_missing=True
    )

    document_url = request.params["document_url"]
    document_url_match = DOCUMENT_URL_REGEX.search(document_url)
    assert document_url_match  # noqa: S101
    document_course_id = document_url_match["course_id"]
    document_file_id = document_url_match["url"]
    effective_file_id = _effective_file_id(
        course_copy_plugin, course, document_url, document_course_id, document_file_id
    )

    # Try to access the file, we have to check that we have indeed access to this file.
    if not api.file_exists(effective_file_id):
        raise FileNotFoundInCourse("moodle_file_not_found_in_course", document_url)  # noqa: EM101

    return {
        "via_url": helpers.via_url(
            request, effective_file_id, content_type="pdf", query={"token": api.token}
        )
    }


def _effective_file_id(
    course_copy_plugin, course, document_url, document_course_id, document_file_id
):
    if course.lms_id == document_course_id:
        # Not in a course copy scenario, use the IDs from the document_url
        LOG.debug("Via URL for file in the same course. %s", document_url)
        return document_file_id

    mapped_file_id = course.get_mapped_file_id(document_file_id)
    if mapped_file_id != document_file_id:
        LOG.debug(
            "Via URL for file already mapped for course copy. Document: %s, course: %s, mapped file: %s",
            document_url,
            course.lms_id,
            mapped_file_id,
        )
        return mapped_file_id

    # In moodle course copy for files is easier to solve because we don't make
    # requests in the name of the user so we can fix it for all launches.
    # It won't only not succeed if the file doesn't have an equivalent file in the new course
    found_file = course_copy_plugin.find_matching_file_in_course(
        document_file_id, course.lms_id
    )
    if not found_file:
        LOG.debug(
            "Via URL for page, couldn't find page in the new course. Document: %s, course: %s.",
            document_url,
            course.lms_id,
        )
        raise FileNotFoundInCourse("moodle_file_not_found_in_course", document_url)  # noqa: EM101
    # Store a mapping so we don't have to re-search next time.
    LOG.debug(
        "Via URL for page, found page in the new course. Document: %s, course: %s, new page id: %s",
        document_url,
        course.lms_id,
        found_file.lms_id,
    )
    course.set_mapped_file_id(document_file_id, found_file.lms_id)
    return found_file.lms_id
