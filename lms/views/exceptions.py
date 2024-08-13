import logging

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
from lms.services import HAPIError, SerializableError
from lms.validation import ValidationError

_ = i18n.TranslationStringFactory(__package__)

LOG = logging.getLogger(__name__)


@view_defaults(path_info=not_("^/api/.*"), renderer="lms:templates/error.html.jinja2")
class ExceptionViews:
    def __init__(self, exception, request):
        self.exception = exception
        self.request = request

    @notfound_view_config(append_slash=True)
    def notfound(self):
        LOG.info("Page not found: %s", self.request.url)
        return self.error_response(404, _("Page not found"))

    @forbidden_view_config()
    def forbidden(self):
        if exception := getattr(self.exception.result, "exception", None):
            # If we have an exception attached to the Denied object
            # we'll treat it the same way the corresponding exception view.
            try:
                self.exception = exception
                raise exception
            except ValidationError:
                LOG.debug("Validation error: %s", exception.messages)
                self.request.override_renderer = (
                    "lms:templates/validation_error.html.jinja2"
                )
                self.request.response.status_int = 403
                return {"error": exception}
            except SerializableError:
                self.request.override_renderer = (
                    "lms:templates/error_dialog.html.jinja2"
                )
                return self.serializable_error()

        return self.error_response(403, _("You're not authorized to view this page"))

    @exception_view_config(context=HTTPClientError)
    def http_client_error(self):
        return self.error_response(self.exception.status_int, str(self.exception))

    @exception_view_config(context=HAPIError)
    def hapi_error(self):
        return self.error_response(500, self.exception.message)

    @exception_view_config(
        context=ValidationError, renderer="lms:templates/validation_error.html.jinja2"
    )
    def validation_error(self):
        self.request.response.status_int = self.exception.status_int
        LOG.info(
            "Validation error: %s. Parameters: %s",
            self.exception.messages,
            self.request.params,
        )
        return {"error": self.exception}

    @exception_view_config(
        ReusedConsumerKey, renderer="lms:templates/error_dialog.html.jinja2"
    )
    def reused_consumer_key(self):
        self.request.response.status_int = 400

        self.request.context.js_config.enable_error_dialog_mode(
            self.request.context.js_config.ErrorCode.REUSED_CONSUMER_KEY,
            error_details={
                "existing_tool_consumer_instance_guid": self.exception.existing_guid,
                "new_tool_consumer_instance_guid": self.exception.new_guid,
            },
        )

        return {}

    @exception_view_config(
        context=SerializableError, renderer="lms:templates/error_dialog.html.jinja2"
    )
    def serializable_error(self):
        self.request.response.status_int = 400

        self.request.context.js_config.enable_error_dialog_mode(
            error_code=self.exception.error_code,
            message=self.exception.message,
            error_details=self.exception.details,
        )

        return {}

    @exception_view_config(context=Exception)
    def error(self):
        LOG.exception("Unexpected error %s", type(self.exception))
        return self.error_response(
            500,
            _(
                "Sorry, but something went wrong. "
                "The issue has been reported and we'll try to "
                "fix it."
            ),
        )

    def error_response(self, status, message):
        """Set the response status and return template data for error.html.jinja2."""
        self.request.response.status_int = status
        return {"message": message}
