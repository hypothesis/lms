import h_pyramid_sentry
from pyramid import httpexceptions, i18n
from pyramid.config import not_
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
)

from lms.models import ReusedConsumerKey
from lms.validation import ValidationError

_ = i18n.TranslationStringFactory(__package__)

DEFAULT_RENDERER = "lms:templates/error.html.jinja2"


def _http_error(exc, request):
    """Handle an HTTP 4xx or 5xx exception."""
    request.response.status_int = exc.status_int
    return {"message": str(exc)}


@notfound_view_config(renderer=DEFAULT_RENDERER)
def notfound(_exc, request):
    request.response.status_int = 404
    return {"message": _("Page not found")}


@forbidden_view_config(renderer=DEFAULT_RENDERER)
def forbidden(_exc, request):
    request.response.status_int = 403
    return {"message": _("You're not authorized to view this page")}


@exception_view_config(
    context=httpexceptions.HTTPClientError, renderer=DEFAULT_RENDERER
)
def http_client_error(exc, request):
    """Handle an HTTP 4xx (client error) exception."""
    return _http_error(exc, request)


@exception_view_config(
    context=httpexceptions.HTTPServerError, renderer=DEFAULT_RENDERER
)
def http_server_error(exc, request):
    """Handle an HTTP 5xx (server error) exception."""
    h_pyramid_sentry.report_exception()
    return _http_error(exc, request)


@exception_view_config(
    context=ValidationError,
    path_info=not_("^/api/.*"),
    renderer="lms:templates/validation_error.html.jinja2",
)
def validation_error(exc, request):
    """Handle a ValidationError."""
    request.response.status_int = exc.status_int
    return {"error": exc}


@exception_view_config(
    ReusedConsumerKey,
    renderer="lms:templates/error_dialog.html.jinja2",
)
def reused_tool_guid_error(exc, request):
    request.context.js_config.enable_error_dialog_mode(
        request.context.js_config.ErrorCode.REUSED_TOOL_GUID,
        error_details={
            "existing_tool_consumer_guid": exc.existing_guid,
            "new_tool_consumer_guid": exc.new_guid,
        },
    )

    return {}


@exception_view_config(context=Exception, renderer=DEFAULT_RENDERER)
def error(_exc, request):
    """
    Handle an unexpected exception.

    If the code raises an unexpected exception (anything not caught by any
    of the more specific exception views above) then we assume it was a
    bug. When this happens we:

    1. Set the response status to 500 Server Error.
    2. Show the user an error page containing only a generic error message
       (don't show them the exception message).

    These issues also get reported to Sentry but we don't have to
    do that here -- non-HTTPError exceptions are automatically
    reported by the Pyramid Sentry integration.
    """
    request.response.status_int = 500
    return {
        "message": _(
            "Sorry, but something went wrong. "
            "The issue has been reported and we'll try to "
            "fix it."
        )
    }
