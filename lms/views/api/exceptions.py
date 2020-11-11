"""Error views for the API."""
from pyramid import i18n
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
    view_defaults,
)

from lms.services import (
    CanvasAPIAccessTokenError,
    CanvasAPIError,
    CanvasAPIPermissionError,
    CanvasFileNotFoundInCourse,
    LTIOutcomesAPIError,
    NoOAuth2Token,
)
from lms.validation import ValidationError

_ = i18n.TranslationStringFactory(__package__)


@view_defaults(renderer="json")
class ExceptionViews:
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

    @exception_view_config(context=NoOAuth2Token)
    @exception_view_config(context=CanvasAPIAccessTokenError)
    def canvas_api_access_token_error(self):
        return self.error_response()

    @exception_view_config(context=CanvasAPIPermissionError)
    @exception_view_config(context=CanvasFileNotFoundInCourse)
    def canvas_api_permission_error(self):
        return self.error_response(
            error_code=self.context.error_code, details=self.context.details
        )

    @exception_view_config(context=CanvasAPIError)
    @exception_view_config(context=LTIOutcomesAPIError)
    def proxy_api_error(self):
        return self.error_response(
            message=self.context.explanation, details=self.context.details
        )

    @exception_view_config(path_info="/api/*", context=Exception)
    def api_error(self):
        """Fallback error handler for frontend API requests."""
        # Exception details are not reported here to avoid leaking internal information.
        return self.error_response(
            500,
            message=_(
                "A problem occurred while handling this request. Hypothesis has been notified."
            ),
        )

    @forbidden_view_config(path_info="/api/*")
    def forbidden(self):
        return self.error_response(
            403, message=_("You're not authorized to view this page.")
        )

    @notfound_view_config(path_info="/api/*")
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
