from lms.product.plugin.misc import MiscPlugin
from urllib.parse import unquote
import re


class CanvasMiscPlugin(MiscPlugin):
    # If the URL looks like "schema%3a" (schema:) it's double-encoded
    # https://www.rfc-editor.org/rfc/rfc3986#section-3.1
    _ENCODED_URL = re.compile("^[a-z][a-z0-9+.-]*%3a", re.IGNORECASE)

    def get_deep_linking_document_url(self, request):
        """
        Get the document URL from deep linked assignment.

        In canvas this always means getting it from an query parameter in the launch URL
        """
        if url := request.params.get("url"):
            # Work around a bug in Canvas's handling of LTI Launch URLs in
            # SpeedGrader launches where query params get double-encoded.
            # See https://github.com/instructure/canvas-lms/issues/1486
            if self._ENCODED_URL.match(url):
                url = unquote(url)

        return url

    def _from_canvas_file(self, request):
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

    def _from_deep_linking_provided_url(self, request):
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

    def get_document_url(self, request):
        for document_url_source in (
            self._from_canvas_file,
            self._from_deep_linking_provided_url,
            self._from_assignment_in_db,
        ):
            if document_url := document_url_source(request):
                return document_url

        return None
