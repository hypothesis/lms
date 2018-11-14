import os

from pyramid import httpexceptions
from pyramid import i18n
from pyramid.settings import asbool
import sentry_sdk

from lms.exceptions import LTILaunchError

_ = i18n.TranslationStringFactory(__package__)


def http_error(exc, request):
    """
    Handle an HTTP 4xx or 5xx exception.

    If code raises HTTPClientError (the base class for all the HTTP 4xx
    errors) or HTTPServerError (base class for 5xx errors), or a subclass
    of either, then we:

    1. Report the error to Sentry.
    2. Set the HTTP response status to the 4xx or 5xx status from the
       exception.
    3. Show the user an error page containing the specific error message
       from the exception.
    """
    sentry_sdk.capture_exception(exc)
    request.response.status_int = exc.status_int
    return {"message": str(exc)}


def lti_launch_error(exc, request):
    """
    Handle an invalid LTI launch request.

    Code raises :exc:`lms.exceptions.LTILaunchError` if there's a problem
    with an LTI launch request, such as a required LTI launch parameter
    missing. When this happens we:

    1. Report the error to Sentry.
    2. Set the HTTP response status code to 400 Bad Request.
    3. Show the user an error page containing the specific error message
    """
    sentry_sdk.capture_exception(exc)
    request.response.status_int = 400
    return {"message": str(exc)}


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
    debug = asbool(os.environ.get("DEBUG") or config.registry.settings.get("debug"))
    if debug:
        # Don't register the error pages in development environments.  Let
        # pyramid_debugtoolbar show the traceback in the browser and terminal
        # instead.
        # If you want to test the error pages in your dev env you can set the
        # environment variable DEBUG to false:
        #     export DEBUG=false
        return

    view_defaults = {"renderer": "lms:templates/error.html.jinja2"}

    config.add_exception_view(
        http_error, context=httpexceptions.HTTPError, **view_defaults
    )
    config.add_exception_view(lti_launch_error, context=LTILaunchError, **view_defaults)
    config.add_exception_view(error, context=Exception, **view_defaults)
