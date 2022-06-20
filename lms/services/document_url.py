import re
from functools import lru_cache
from typing import Optional
from urllib.parse import unquote

from lms.services.vitalsource import VitalSourceService


class DocumentURLService:
    """A service for getting LTI launch document URLs."""

    def __init__(self, assignment_service):
        self._assignment_service = assignment_service

    @lru_cache(1)
    def get_document_url(self, context, request) -> Optional[str]:
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
            if document_url := document_url_source(context, request):
                return document_url

        return None

    _ENCODED_URL = re.compile("^(?:https?|canvas|vitalsource)%3a", re.IGNORECASE)

    @classmethod
    def _from_deep_linking_provided_url(cls, _context, request):
        """Get the URL from our own configuration set during deep linking."""

        if url := request.params.get("url"):
            # Work around a bug in Canvas's handling of LTI Launch URLs in
            # SpeedGrader launches where query params get double-encoded.
            # See https://github.com/instructure/canvas-lms/issues/1486
            if cls._ENCODED_URL.match(url):
                url = unquote(url)

        return url

    @classmethod
    def _from_canvas_file(cls, context, request):
        """Get a Canvas file URL based on temporary data passed from Canvas."""

        if request.params.get("canvas_file"):
            course_id = context.lti_params["custom_canvas_course_id"]
            file_id = request.params["file_id"]

            return f"canvas://file/course/{course_id}/file_id/{file_id}"

        return None

    @classmethod
    def _from_legacy_vitalsource_book(cls, _context, request):
        """
        Respond to a legacy configured VitalSource assignment.

        Newer Vitalsource assignments are configured with document URLs like
        `vitalsource://...`
        """
        if request.params.get("vitalsource_book"):
            return VitalSourceService.generate_document_url(
                book_id=request.params["book_id"],
                cfi=request.params.get("cfi"),
            )

        return None

    def _from_assignment_in_db(self, context, _request):
        """Get a document URL from an assignment in the DB matching a param."""

        for param in (
            "resource_link_id",  # A normal LTI (non-deep linked) launch
            "ext_d2l_resource_link_id_history",  # A Brightspace course we can copy
            "resource_link_id_history",  # A Blackboard course we can copy
        ):
            # Horrible work around
            if param == "resource_link_id":
                resource_link_id = context.resource_link_id
            else:
                resource_link_id = context.lti_params.get(param)

            if resource_link_id and (
                assigment := self._assignment_service.get_assignment(
                    tool_consumer_instance_guid=context.lti_params.get(
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
