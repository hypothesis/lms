from pyramid import httpexceptions
from pyramid import i18n
from pyramid.view import exception_view_config
from pyramid.view import view_defaults

from lms.exceptions import LTILaunchError

_ = i18n.TranslationStringFactory(__package__)


@view_defaults(renderer="lms:templates/error.html.jinja2")
class ErrorViews:
    def __init__(self, exc, request):
        self.exc = exc
        self.request = request

    @exception_view_config(httpexceptions.HTTPError)
    @exception_view_config(httpexceptions.HTTPServerError)
    def httperror(self):
        """
        Handle an HTTP 4xx or 5xx exception.

        If code raises an HTTP client or server error we assume this was
        deliberately raised We show the user an error page including specific
        error message but _do not_ report the error to Sentry
        """
        self.request.response.status_int = self.exc.status_int
        return {"message": str(self.exc)}

    @exception_view_config(LTILaunchError)
    def missing_lti_param_error(self):
        """
        Handle LTILaunchErrors.

        If code raises an LTILaunchError we assume this was deliberately raised
        because an invalid LTI launch request was received. For example a
        required LTI launch parameter was missing. We return a 400 Bad Request
        response, show the user an error page with the specific error message,
        and report the issue to Sentry.
        """
        self.request.response.status_int = 400
        self.request.raven.captureException()
        return {"message": str(self.exc)}

    @exception_view_config(Exception)
    def error(self):
        """
        Handle an unexpected exception.

        If the code raises an unexpected exception (anything not caught by any
        of the more specific exception views above) then we assume it was a
        bug.  We show the user a generic error page and report the exception to
        Sentry.
        """
        self.request.response.status_int = 500
        self.request.raven.captureException()
        return {
            "message": _(
                "Sorry, but something went wrong. "
                "The issue has been reported and we'll try to "
                "fix it."
            )
        }
