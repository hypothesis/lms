"""Error views for the API."""
from urllib.parse import urlparse, urlunparse

import sentry_sdk
from h_pyramid_sentry import report_exception
from pyramid import i18n
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
    view_defaults,
)

from lms.services import (
    CanvasAPIPermissionError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.validation import ValidationError

_ = i18n.TranslationStringFactory(__package__)


@view_defaults(path_info="^/api/.*", renderer="json")
class APIExceptionViews:
    """
    Exception views for the API.

    Error responses from the API have JSON bodies with the following keys (all
    optional):

    1. "error_code": A unique string that identifies the error to the frontend.

       If "error_code" is present the frontend should show an error dialog
       relevant to the particular error code. For example if "error_code" is
       "canvas_api_permission_error" the frontend should show a
       "You don't have permission" error dialog. The error dialog should
       include a [Try again] button that opens the "canvas_api.oauth.authorize"
       route.

    2. "message": An error message for the frontend to show to the user.

       If "message" is present the frontend will show an error dialog that
       indicates that something went wrong and has a [Try again] button that
       opens the "canvas_api.oauth.authorize" route. The "message" string
       should be rendered by the frontend somewhere in the error dialog.

    If no "error_code" or "message" is present the frontend will show a
    standard authorization dialog (not an error dialog) and the button that
    opens "canvas_api.oauth.authorize" route will be labelled [Authorize].

    3. "details": Optional further error details to show to the user in the
       error dialog, for debugging and support.

    The HTTP status codes of the API error responses are:

    * 403 Forbidden is used if the frontend's authentication to the backend's
      API failed

    * 400 Bad Request is deliberately abused whenever the backend's
      server-to-server request to a third-party API (such as the Canvas API or
      the Blackboard API) fails or can't be made for any reason.

      For example if we can't authenticate to the third-party API because we
      don't have an access token for this user yet; if we get an authentication
      error from the third-party API because the access token has expired (and
      can't be refreshed); if the third-party API returns an invalid,
      unexpected or unsuccessful response; are all 400s.

      The frontend uses the JSON bodies of these 400 Bad Request responses to
      distinguish between them and decide what to do.

      Since 403 is used to mean that the frontend's authentication *to the
      backend* failed, it can't also be used to indicate failure of the
      backend's server-to-server request to authenticate with the third-party
      API. Hence why 400 is used for this.

      You might think that some sort of gateway error (e.g. 502 Bad Gateway) is
      more semantically correct than abusing 400 here. But Cloudflare replaces
      502 JSON responses from our app with its own Cloudflare error pages. So
      we can't use 5xx statuses in production.

    * 422 is used for validation errors (if the frontend sent invalid params to
      a backend API) (in practice this should never happen)

    * 404 Not Found is used for API endpoints that don't exist
      (in practice this should never happen)

    * 500 Server Error is used for unexpected exceptions (our code crashed)
      (in practice this should never happen)

    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @exception_view_config(context=ValidationError)
    def validation_error(self):
        return self.error_response(
            422, message=self.context.explanation, details=self.context.messages
        )

    @exception_view_config(context=ExternalRequestError)
    def external_request_error(self):
        sentry_sdk.set_context(
            "request",
            {
                "method": self.context.method,
                "url": self.context.url,
                "body": self.context.request_body,
            },
        )
        sentry_sdk.set_context(
            "response",
            {
                "status_code": self.context.status_code,
                "reason": self.context.reason,
                "body": self.context.response_body,
            },
        )
        sentry_sdk.set_context("validation_errors", self.context.validation_errors)

        report_exception()

        # It's important that this exception view always returns a non-empty
        # message even if ExternalRequestError.message is None because an error
        # response JSON body of {} tells the frontend to show the authorization
        # dialog, whereas {"message": "..."} tells the frontend to show the
        # error dialog.
        message = self.context.message or "External request failed"

        return self.error_response(
            message=message,
            details={
                "request": {
                    "method": self.context.method,
                    "url": strip_queryparams(self.context.url),
                },
                "response": {
                    "status_code": self.context.status_code,
                    "reason": self.context.reason,
                },
                "validation_errors": self.context.validation_errors,
            },
        )

    @exception_view_config(context=OAuth2TokenError)
    def oauth2_token_error(self):
        return self.error_response()

    @exception_view_config(context=HTTPBadRequest)
    def http_bad_request(self):
        return self.error_response(
            status=self.context.code, message=self.context.detail
        )

    @exception_view_config(
        # It's unfortunately necessary to mention CanvasAPIPermissionError
        # specifically here because otherwise the external_request_error()
        # exception view above would catch CanvasAPIPermissionError's.
        context=CanvasAPIPermissionError
    )
    @exception_view_config(context=Exception)
    def api_error(self):
        """
        General fallback error handler for API requests.

        If the exception has an `error_code` attribute then:

        1. The `error_code` attribute will be used as the "error_code" field in
           the response's JSON body

        2. The response's HTTP status will be 400

        3. If the exception also has a `details` attribute this will be used as
           "details" field in the response's body

        If the exception does not have an `error_code` attribute then:

        1. The response's HTTP status will be 500

        2. A fixed string (see below) will be used as the "message" field in
           the response's JSON body
        """

        if hasattr(self.context, "error_code"):
            return self.error_response(
                error_code=self.context.error_code,
                details=getattr(self.context, "details", None),
            )

        # Exception details are not reported here to avoid leaking internal information.
        return self.error_response(
            500,
            message=_(
                "A problem occurred while handling this request. Hypothesis has been notified."
            ),
        )

    @forbidden_view_config()
    def forbidden(self):
        return self.error_response(
            403, message=_("You're not authorized to view this page.")
        )

    @notfound_view_config()
    def notfound(self):
        return self.error_response(404, message=_("Endpoint not found."))

    def error_response(self, status=400, error_code=None, message=None, details=None):
        self.request.response.status_int = status

        response = {}

        if error_code is not None:
            response["error_code"] = error_code

        if message is not None:
            response["message"] = message

        if details is not None:
            response["details"] = details

        return response


def strip_queryparams(url):
    """Return `url` with any query params removed."""
    if not url:
        return url

    return urlunparse(urlparse(url)._replace(query={}))
