import re

from pyramid.view import view_config

from lms.security import Permissions
from lms.services.d2l_api import D2LAPIClient
from lms.services.exceptions import FileNotFoundInCourse
from lms.views import helpers

DOCUMENT_URL_REGEX = re.compile(
    r"d2l:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)\/"
)


@view_config(
    request_method="GET",
    route_name="d2l_api.courses.files.list",
    renderer="json",
    permission=Permissions.API,
)
def list_files(_context, request):
    """Return the list of files in the given course."""
    return request.find_service(D2LAPIClient).list_files(request.matchdict["course_id"])


@view_config(
    request_method="GET",
    route_name="d2l_api.courses.files.via_url",
    renderer="json",
    permission=Permissions.API,
)
def via_url(_context, request):
    course_copy_plugin = request.product.plugin.course_copy
    api_client = request.find_service(D2LAPIClient)

    course_id = request.matchdict["course_id"]
    document_url = request.params["document_url"]

    course = request.find_service(name="course").get_by_context_id(
        course_id, raise_on_missing=True
    )

    document_url_match = DOCUMENT_URL_REGEX.search(document_url)
    assert document_url_match  # noqa: S101
    file_id = course.get_mapped_file_id(document_url_match["file_id"])
    try:
        if request.lti_user.is_instructor:  # noqa: SIM102
            if not course_copy_plugin.is_file_in_course(course_id, file_id):
                raise FileNotFoundInCourse(  # noqa: TRY301
                    "d2l_file_not_found_in_course_instructor",
                    file_id,
                )

        public_url = api_client.public_url(course_id, file_id)

    except FileNotFoundInCourse:
        found_file = course_copy_plugin.find_matching_file_in_course(file_id, course_id)
        if not found_file:
            raise

        # Try again to return a public URL, this time using found_file_id.
        public_url = api_client.public_url(course_id, found_file.lms_id)

        # Store a mapping so we don't have to re-search next time.
        course.set_mapped_file_id(file_id, found_file.lms_id)

    access_token = request.find_service(name="oauth2_token").get().access_token
    headers = {"Authorization": f"Bearer {access_token}"}
    return {
        "via_url": helpers.via_url(
            request, public_url, content_type="pdf", headers=headers
        )
    }
