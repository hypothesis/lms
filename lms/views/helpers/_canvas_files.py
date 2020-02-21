"""Helpers for working with the Canvas Files API."""
from lms.services import ConsumerKeyError

__all__ = ("canvas_files_available",)


def canvas_files_available(request):
    """Return True if the Canvas Files API is available to this request."""
    try:
        developer_key = request.find_service(name="ai_getter").developer_key(
            request.params.get("oauth_consumer_key")
        )
    except ConsumerKeyError:
        return False

    return "custom_canvas_course_id" in request.params and developer_key is not None
