"""
Views for getting OAuth 2 access tokens for the Canvas API.

This module provides views for doing an OAuth 2 flow to get a Canvas API access
token for the current user:

https://canvas.instructure.com/doc/api/file.oauth.html

The received access tokens are saved to the DB and used by proxy API views to
authenticated server-to-server requests to Canvas.
"""
from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError
from pyramid.view import exception_view_config, view_config

from lms.resources import FrontendAppResource
from lms.services import CanvasAPIServerError
from lms.validation.authentication import CanvasOAuthCallbackSchema

#: The Canvas API scopes that we need for our Canvas Files feature.
FILES_SCOPES = (
    "url:GET|/api/v1/courses/:course_id/files",
    "url:GET|/api/v1/files/:id/public_url",
)

#: The Canvas API scopes that we need for our Sections feature.
SECTIONS_SCOPES = (
    "url:GET|/api/v1/courses/:id",
    "url:GET|/api/v1/courses/:course_id/sections",
    "url:GET|/api/v1/courses/:course_id/users/:id",
)


@view_config(
    request_method="GET", route_name="canvas_api.authorize", permission="canvas_api"
)
def authorize(request):
    ai_getter = request.find_service(name="ai_getter")
    course_service = request.find_service(name="course")

    scopes = FILES_SCOPES

    if ai_getter.canvas_sections_supported() and (
        # If the instance could add a new course with sections...
        ai_getter.settings().get("canvas", "sections_enabled")
        # ... or any of it's existing courses have sections
        or course_service.any_with_setting("canvas", "sections_enabled", True)
    ):
        scopes += SECTIONS_SCOPES

    authorize_url = urlunparse(
        (
            "https",
            urlparse(ai_getter.lms_url()).netloc,
            "login/oauth2/auth",
            "",
            urlencode(
                {
                    "client_id": ai_getter.developer_key(),
                    "response_type": "code",
                    "redirect_uri": request.route_url("canvas_oauth_callback"),
                    "state": CanvasOAuthCallbackSchema(request).state_param(),
                    "scope": " ".join(scopes),
                }
            ),
            "",
        )
    )

    return HTTPFound(location=authorize_url)


@view_config(
    request_method="GET",
    route_name="canvas_oauth_callback",
    permission="canvas_api",
    renderer="lms:templates/api/canvas/oauth2_redirect.html.jinja2",
    schema=CanvasOAuthCallbackSchema,
)
def oauth2_redirect(request):
    authorization_code = request.parsed_params["code"]
    canvas_api_client = request.find_service(name="canvas_api_client")

    try:
        canvas_api_client.get_token(authorization_code)
    except CanvasAPIServerError as err:
        raise HTTPInternalServerError("Authorizing with the Canvas API failed") from err

    return {}


@exception_view_config(
    request_method="GET",
    route_name="canvas_oauth_callback",
    renderer="lms:templates/api/canvas/oauth2_redirect_error.html.jinja2",
)
@exception_view_config(
    request_method="GET",
    route_name="canvas_api.authorize",
    renderer="lms:templates/api/canvas/oauth2_redirect_error.html.jinja2",
)
def oauth2_redirect_error(request):
    # In an exception view the `context` is usually the exception that occurred.
    # We're going to cheat here and create a different object instead to serve
    # as the `context` in templates.
    context = FrontendAppResource(request)
    context.js_config.enable_oauth_error_mode(
        error_details=request.params.get("error_description"),
        is_scope_invalid=request.params.get("error") == "invalid_scope",
        requested_scopes=FILES_SCOPES + SECTIONS_SCOPES,
    )
    return {"context": context}
