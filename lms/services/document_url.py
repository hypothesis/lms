import re
from functools import lru_cache
from typing import Optional
from urllib.parse import unquote

from lms.services.assignment import AssignmentService
from lms.services.vitalsource import VSBookLocation


class DocumentURLService:
    """A service for getting LTI launch document URLs."""

    def __init__(self, assignment_service: AssignmentService):
        self._assignment_service = assignment_service

    @lru_cache(1)
    def get_document_url(self, request) -> Optional[str]:
        """
        Get the configured document for this LTI launch.

        This will try all known methods for finding out, and will return None
        if no configuration can be found.
        """
        for document_url_source in (
            self._from_deep_linking_provided_url,
            self._from_canvas_file,
            self._from_legacy_vitalsource_book,
            self._from_assignment_in_db,
        ):
            if document_url := document_url_source(request):
                return document_url

        return None

    # If the URL looks like "schema%3a" (schema:) it's double-encoded
    # https://www.rfc-editor.org/rfc/rfc3986#section-3.1
    _ENCODED_URL = re.compile("^[a-z][a-z0-9+.-]*%3a", re.IGNORECASE)

    @classmethod
    def _from_deep_linking_provided_url(cls, request):
        """
        Get the URL from the deep linking information.

        This is the parameter we send during deep linking configuration coming
        back to us from the LMS.
        """

        if url := request.params.get("url"):
            # Work around a bug in Canvas's handling of LTI Launch URLs in
            # SpeedGrader launches where query params get double-encoded.
            # See https://github.com/instructure/canvas-lms/issues/1486
            if cls._ENCODED_URL.match(url):
                url = unquote(url)

        return url

    @classmethod
    def _from_canvas_file(cls, request):
        """
        Get a Canvas file URL.

        These values are ephemeral and can't be stored.
        """

        if (
            request.params.get("canvas_file")
            and (course_id := request.lti_params.get("custom_canvas_course_id"))
            and (file_id := request.params["file_id"])
        ):
            return f"canvas://file/course/{course_id}/file_id/{file_id}"

        return None

    @classmethod
    def _from_legacy_vitalsource_book(cls, request):
        """
        Respond to a legacy configured VitalSource assignment.

        Newer Vitalsource assignments are configured with document URLs like
        `vitalsource://...`
        """
        if request.params.get("vitalsource_book"):
            return VSBookLocation(
                book_id=request.params["book_id"],
                cfi=request.params.get("cfi"),
            ).document_url

        return None

    def _from_assignment_in_db(self, request):
        """Get a document URL from an assignment in the DB matching a param."""

        for param in (
            "resource_link_id",  # A normal LTI (non-deep linked) launch
            "resource_link_id_history",  # A Blackboard course we can copy
            "ext_d2l_resource_link_id_history",  # Ditto for Brightspace
        ):
            if (resource_link_id := request.lti_params.get(param)) and (
                assigment := self._assignment_service.get_assignment(
                    tool_consumer_instance_guid=request.lti_params.get(
                        "tool_consumer_instance_guid"
                    ),
                    resource_link_id=resource_link_id,
                )
            ):
                return assigment.document_url

        return None


def factory(_context, request):
    return DocumentURLService(
        assignment_service=request.find_service(name="assignment")
    )
