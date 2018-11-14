from pyramid import httpexceptions
from pyramid import i18n
from pyramid.view import exception_view_config
from pyramid.view import view_defaults
import sentry_sdk

from lms.exceptions import LTILaunchError

_ = i18n.TranslationStringFactory(__package__)


@view_defaults(renderer="lms:templates/error.html.jinja2")
class ErrorViews:
    def __init__(self, exc, request):
        self.exc = exc
        self.request = request

    @exception_view_config(httpexceptions.HTTPError)
    def http_error(self):
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
        sentry_sdk.capture_exception(self.exc)
        self.request.response.status_int = self.exc.status_int
        return {"message": str(self.exc)}

    @exception_view_config(LTILaunchError)
    def lti_launch_error(self):
        """
        Handle an invalid LTI launch request.

        Code raises :exc:`lms.exceptions.LTILaunchError` if there's a problem
        with an LTI launch request, such as a required LTI launch parameter
        missing. When this happens we:

        1. Report the error to Sentry.
        2. Set the HTTP response status code to 400 Bad Request.
        3. Show the user an error page containing the specific error message
        """
        sentry_sdk.capture_exception(self.exc)
        self.request.response.status_int = 400
        return {"message": str(self.exc)}

    @exception_view_config(Exception)
    def error(self):
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
        self.request.response.status_int = 500
        return {
            "message": _(
                "Sorry, but something went wrong. "
                "The issue has been reported and we'll try to "
                "fix it."
            )
        }
