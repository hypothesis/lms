"""Error views for the API."""

import logging
from dataclasses import asdict, dataclass
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

from lms.error_code import ErrorCode
from lms.events import LTIEvent
from lms.services import (
    CanvasAPIPermissionError,
    EventService,
    ExternalAsyncRequestError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.services.exceptions import ConcurrentTokenRefreshError, SerializableError
from lms.validation import ValidationError

_ = i18n.TranslationStringFactory(__package__)


LOG = logging.getLogger(__name__)


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
       include a [Try again] button that opens the OAuth 2 authorize
       route.

    2. "message": An error message for the frontend to show to the user.

       If "message" is present the frontend will show an error dialog that
       indicates that something went wrong and has a [Try again] button that
       opens the OAuth 2 authorize route. The "message" string
       should be rendered by the frontend somewhere in the error dialog.

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

        # 400 is the default status for error responses.
        # Some of the views below override this.
        self.request.response.status_int = 400

    @exception_view_config(context=ConcurrentTokenRefreshError)
    def concurrent_token_refresh_error(self):
        self.request.response.status_int = 409
        return ErrorBody(
            error_code="concurrent_token_refresh",
            message="API token is already being refreshed",
        )

    @exception_view_config(context=ValidationError)
    def validation_error(self):
        self.request.response.status_int = 422
        return ErrorBody(
            message=self.context.explanation, details=self.context.messages
        )

    @exception_view_config(context=ExternalRequestError)
    @exception_view_config(context=ExternalAsyncRequestError)
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

        return ErrorBody(
            message=self.context.message,
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
        LOG.debug("Exception view for: OAuth2TokenError")
        return ErrorBody(error_code=ErrorCode.OAUTH2_AUTHORIZATION_ERROR)

    @exception_view_config(context=HTTPBadRequest)
    def http_bad_request(self):
        self.request.response.status_int = self.context.code
        return ErrorBody(message=self.context.detail)

    @exception_view_config(
        # It's unfortunately necessary to mention CanvasAPIPermissionError
        # specifically here because otherwise the external_request_error()
        # exception view above would catch CanvasAPIPermissionError's.
        context=CanvasAPIPermissionError
    )
    @exception_view_config(context=Exception)
    @exception_view_config(context=SerializableError)
    def api_error(self):
        """
        General fallback error handler for API requests.

        If the exception has an `error_code` attribute then:

        1. The `error_code` attribute will be used as the "error_code" field in
           the response's JSON body
        2. The response's HTTP status will be 400
        3. If the exception also has a `details` attribute this will be used as
           "details" field in the response's body

        You can use `SerializableError` or a child if you'd like to trigger
        this conveniently.

        If the exception does not have an `error_code` attribute then:
        1. The response's HTTP status will be 500
        2. A fixed string (see below) will be used as the "message" field in
           the response's JSON body
        """

        if hasattr(self.context, "error_code"):
            EventService.queue_event(
                LTIEvent.from_request(
                    request=self.request,
                    type_=LTIEvent.Type.ERROR_CODE,
                    data={"code": self.context.error_code},
                )
            )

            return ErrorBody(
                error_code=self.context.error_code,
                message=getattr(self.context, "message", None),
                details=getattr(self.context, "details", None),
            )

        # Exception details are not reported here to avoid leaking internal information.
        self.request.response.status_int = 500
        return ErrorBody(
            message=_(
                "A problem occurred while handling this request. Hypothesis has been notified."
            ),
        )

    @forbidden_view_config()
    def forbidden(self):
        self.request.response.status_int = 403
        return ErrorBody(message=_("You're not authorized to view this page."))

    @notfound_view_config()
    def notfound(self):
        LOG.info("Page not found: %s", self.request.url)
        self.request.response.status_int = 404
        return ErrorBody(message=_("Endpoint not found."))


@dataclass
class ErrorBody:
    error_code: str | None = None
    message: str | None = None
    details: dict | None = None

    def __json__(self, request):
        """
        Return a JSON-serializable representation of this error response body.

        If a view with renderer="json" returns an ErrorBody object then
        Pyramid's JSON renderer will call this method to get an object to
        JSON-serialize for the response body. See:
        https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/renderers.html#using-a-custom-json-method
        """
        body = {key: value for key, value in asdict(self).items() if value is not None}

        # If the exception is refreshable add refresh API info for the frontend.
        # This tells the frontend to try making a refresh request then
        # re-trying the original request.
        if getattr(request.exception, "refreshable", False):
            oauth2_token_service = request.find_service(name="oauth2_token")

            refresh_route = getattr(request.exception, "refresh_route", None)
            if refresh_route is None:
                refresh_route = request.product.route.oauth2_refresh

            # Test if this user has an existing access token that we can refresh.
            if refresh_route == "canvas_studio_api.oauth.refresh_admin":
                # This refresh is for a user that is different than the current
                # user, so don't try to look up an access token for them.
                can_refresh = True
            else:
                try:
                    kwargs = {}
                    if service := getattr(request.exception, "refresh_service", None):
                        kwargs["service"] = service
                    oauth2_token_service.get(**kwargs)
                    can_refresh = True
                except OAuth2TokenError:
                    can_refresh = False

            if can_refresh:
                if refresh_route:
                    path = request.route_path(refresh_route)
                else:
                    raise ValueError(  # noqa: TRY003
                        f"No OAuth 2 refresh API for {request.product.family}"  # noqa: EM102
                    )
                body["refresh"] = {"method": "POST", "path": path}

        # Expose whether or not the exception is retryable to the frontend.
        if getattr(request.exception, "retryable", False):
            body["retryable"] = True

        return body


def strip_queryparams(url):
    """Return `url` with any query params removed."""
    if not url:
        return url

    return urlunparse(urlparse(url)._replace(query={}))
