"""Error views for the API."""
from pyramid import i18n
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
)

from lms.services import CanvasAPIError, CanvasAPIAccessTokenError


_ = i18n.TranslationStringFactory(__package__)


@exception_view_config(context=CanvasAPIAccessTokenError, renderer="json")
def canvas_api_access_token_error(request):
    request.response.status_int = 400
    # For a CanvasAPIAccessTokenError we don't send any error message or
    # details to the frontend because we don't want the frontend to show any
    # error message to the user in this case. Just the 400 status so the
    # frontend knows that the request failed, and that it should show the user
    # an [Authorize] button so they can get a (new) access token and try again.
    return {"error_message": None, "details": None}


@exception_view_config(context=CanvasAPIError, renderer="json")
def canvas_api_error(context, request):
    request.response.status_int = 400
    # Send the frontend an error message and details to show to the user for
    # debugging.
    return {"error_message": context.explanation, "details": context.details}


@forbidden_view_config(path_info="/api/*", renderer="json")
def forbidden(request):
    request.response.status_int = 403
    return {"message": _("You're not authorized to view this page")}


@notfound_view_config(path_info="/api/*", renderer="json")
def notfound(request):
    request.response.status_int = 404
    return {"message": _("Endpoint not found")}
