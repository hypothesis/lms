import logging

LOG = logging.getLogger(__name__)


def log_retries_callback(request):
    """Log a message when a retried requests succeeds."""
    if (
        request.headers.get("Retry-Count")
        and request.response.status_code >= 200
        and request.response.status_code < 300
    ):
        LOG.debug(
            "Request to %s succeeded after %s retries",
            request.path_info,
            request.headers["Retry-Count"],
        )
