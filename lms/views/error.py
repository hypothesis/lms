import sentry_sdk
from pyramid import httpexceptions, i18n
from pyramid.view import forbidden_view_config, notfound_view_config

from lms.validation import ValidationError

_ = i18n.TranslationStringFactory(__package__)


@notfound_view_config(renderer="lms:templates/error.html.jinja2")
def notfound(request):
    request.response.status_int = 404
    return {"message": _("Page not found")}


@forbidden_view_config(renderer="lms:templates/error.html.jinja2")
def forbidden(request):
    request.response.status_int = 403
    return {"message": _("You're not authorized to view this page")}


def _http_error(exc, request):
    """Handle an HTTP 4xx or 5xx exception."""
    request.response.status_int = exc.status_int
    return {"message": str(exc)}


def http_client_error(exc, request):
    """Handle an HTTP 4xx (client error) exception."""
    return _http_error(exc, request)


def http_server_error(exc, request):
    """Handle an HTTP 5xx (server error) exception."""
    sentry_sdk.capture_exception(exc)
    return _http_error(exc, request)


def validation_error(exc, request):
    """Handle a ValidationError."""
    request.response.status_int = exc.status_int
    return {"error": exc}


def error(request):
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


def includeme(config):
    view_defaults = {"renderer": "lms:templates/error.html.jinja2"}

    config.add_exception_view(
        http_client_error, context=httpexceptions.HTTPClientError, **view_defaults
    )
    config.add_exception_view(
        http_server_error, context=httpexceptions.HTTPServerError, **view_defaults
    )
    config.add_exception_view(error, context=Exception, **view_defaults)

    validation_view_defaults = dict(view_defaults)
    validation_view_defaults["renderer"] = "lms:templates/validation_error.html.jinja2"

    config.add_exception_view(
        validation_error, context=ValidationError, **validation_view_defaults
    )
