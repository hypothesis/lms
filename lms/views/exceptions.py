from pyramid import i18n
from pyramid.config import not_
from pyramid.httpexceptions import HTTPClientError
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
    view_defaults,
)

from lms.models import ReusedConsumerKey
from lms.services import HAPIError
from lms.validation import ValidationError

_ = i18n.TranslationStringFactory(__package__)


@view_defaults(path_info=not_("^/api/.*"), renderer="lms:templates/error.html.jinja2")
class ExceptionViews:
    def __init__(self, exception, request):
        self.exception = exception
        self.request = request

    @notfound_view_config()
    def notfound(self):
        self.request.response.status_int = 404
        return {"message": _("Page not found")}

    @forbidden_view_config()
    def forbidden(self):
        self.request.response.status_int = 403
        return {"message": _("You're not authorized to view this page")}

    @exception_view_config(context=HTTPClientError)
    def http_client_error(self):
        """Handle an HTTP 4xx (client error) exception."""
        self.request.response.status_int = self.exception.status_int
        return {"message": str(self.exception)}

    @exception_view_config(context=HAPIError)
    def hapi_error(self):
        self.request.response.status_int = 500
        return {"message": str(self.exception)}

    @exception_view_config(
        context=ValidationError, renderer="lms:templates/validation_error.html.jinja2"
    )
    def validation_error(self):
        """Handle a ValidationError."""
        self.request.response.status_int = self.exception.status_int
        return {"error": self.exception}

    @exception_view_config(
        ReusedConsumerKey, renderer="lms:templates/error_dialog.html.jinja2"
    )
    def reused_tool_guid_error(self):
        self.request.context.js_config.enable_error_dialog_mode(
            self.request.context.js_config.ErrorCode.REUSED_TOOL_GUID,
            error_details={
                "existing_tool_consumer_guid": self.exception.existing_guid,
                "new_tool_consumer_guid": self.exception.new_guid,
            },
        )

        return {}

    @exception_view_config(context=Exception)
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
